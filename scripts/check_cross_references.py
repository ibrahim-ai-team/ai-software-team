#!/usr/bin/env python3
"""Check command references and agent frontmatter without network access.

- Commands and agents: every backticked hyphenated name must be an existing
  agent, skill or command, and every backticked repository path must exist.
- The orchestrator must name every manifest-required agent it delegates to.
- Agents: frontmatter keys must be known, `name` must match the file name and
  an optional `model` must be a documented alias or a claude-* model ID.
Tool allowlists are already validated by validate_team.py.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Documented subagent frontmatter fields (code.claude.com/docs/en/sub-agents, checked 2026-10-19).
AGENT_KEYS = {
    "name",
    "description",
    "tools",
    "disallowedTools",
    "model",
    "permissionMode",
    "maxTurns",
    "autoCompactWindow",
    "skills",
    "mcpServers",
    "hooks",
    "memory",
    "background",
    "omitClaudeMd",
    "effort",
    "isolation",
    "color",
    "initialPrompt",
    "experimental",
}
MODEL_ALIASES = {"inherit", "sonnet", "opus", "haiku", "fable"}
MODEL_ID = re.compile(r"^claude-[a-z0-9.-]+$")
CODE_SPAN = re.compile(r"`([^`\s]+)`")
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
PATH = re.compile(r"^\.?[\w.-]+(?:/[\w.*-]+)+$")


def frontmatter(text: str) -> list[tuple[int, str, str]]:
    if not text.startswith("---\n"):
        return []
    fields = []
    for line_number, line in enumerate(text.splitlines()[1:], 2):
        if line.strip() == "---":
            break
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            fields.append((line_number, key.strip(), value.strip()))
    return fields


def check(root: Path) -> list[str]:
    errors: list[str] = []
    claude = root / ".claude"
    agents = sorted((claude / "agents").glob("*.md"))
    known_names = {path.stem for path in agents}
    known_names |= {path.name for path in (claude / "skills").glob("*") if (path / "SKILL.md").is_file()}
    known_names |= {path.stem for path in (claude / "commands").glob("*.md")}

    for path in agents:
        shown = path.relative_to(root)
        fields = frontmatter(path.read_text(encoding="utf-8"))
        if not fields:
            errors.append(f"{shown}:1: missing frontmatter")
        for line_number, key, value in fields:
            if key not in AGENT_KEYS:
                errors.append(f"{shown}:{line_number}: unknown frontmatter key '{key}'")
            elif key == "name" and value != path.stem:
                errors.append(f"{shown}:{line_number}: name '{value}' does not match file name '{path.stem}'")
            elif key == "model" and value not in MODEL_ALIASES and not MODEL_ID.match(value):
                errors.append(
                    f"{shown}:{line_number}: model '{value}' is not an alias {sorted(MODEL_ALIASES)} or a claude-* model ID"
                )

    orchestrator = claude / "agents" / "agile-orchestrator.md"
    if orchestrator.is_file():
        manifest = json.loads((claude / "manifest.json").read_text(encoding="utf-8"))
        named = set(CODE_SPAN.findall(orchestrator.read_text(encoding="utf-8")))
        for required in manifest.get("inventory", {}).get("agents", {}).get("required", []):
            role = required.removesuffix(".md")
            if role != "agile-orchestrator" and role not in named:
                errors.append(
                    f"{orchestrator.relative_to(root)}: does not name required agent '{role}', so it cannot delegate to it"
                )

    for path in sorted((claude / "commands").glob("*.md")) + agents:
        shown = path.relative_to(root)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for token in CODE_SPAN.findall(line):
                if PATH.match(token) and "*" not in token:
                    # The status snapshot is a generated runtime artifact; its
                    # absence in a clean checkout is an expected degraded state.
                    generated_paths = {"state/effective.json"}
                    if token not in generated_paths and not (root / token).exists():
                        errors.append(f"{shown}:{line_number}: missing referenced path '{token}'")
                elif NAME.match(token) and token not in known_names:
                    errors.append(f"{shown}:{line_number}: unknown agent/skill/command '{token}'")
    return errors


if __name__ == "__main__":
    failures = check(ROOT)
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print("Cross-reference check passed.")
