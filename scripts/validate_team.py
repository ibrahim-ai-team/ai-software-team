#!/usr/bin/env python3
"""Static validation for the reusable Claude Code AI team starter kit.

Checks inventories, non-empty content, frontmatter, permission guardrails,
CI security settings, and critical orchestration contract markers. Static
validation cannot prove Claude Code runtime behavior or GitHub owner settings.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TOOLS = {"Agent", "Read", "Grep", "Glob", "Edit", "Write", "Bash", "WebSearch", "WebFetch"}
ORCHESTRATOR = "agile-orchestrator"  # the only agent allowed to delegate (Agent tool)
# Reviewers must not be able to change what they review; enforced through their tools allowlist.
READ_ONLY_AGENTS = {"code-review-security", "tech-lead"}
HARD_MINIMUMS = {"agents": 18, "skills": 22}
MANIFEST_PATH = ROOT / ".claude" / "manifest.json"
errors: list[str] = []


def load_manifest() -> dict:
    """Load and validate the declarative inventory manifest."""
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot load .claude/manifest.json: {exc}")
        return {}
    if not isinstance(manifest, dict):
        errors.append("Manifest root must be a JSON object")
        return {}
    if manifest.get("schema_version") != 1:
        errors.append("Unsupported or missing manifest schema_version (expected 1)")
    inventory = manifest.get("inventory")
    if not isinstance(inventory, dict):
        errors.append("Manifest inventory must be an object")
        return {}
    for kind in ("agents", "skills", "commands", "templates"):
        spec = inventory.get(kind)
        if not isinstance(spec, dict):
            errors.append(f"Manifest inventory.{kind} must be an object")
            continue
        if not isinstance(spec.get("directory"), str) or not isinstance(spec.get("pattern"), str):
            errors.append(f"Manifest inventory.{kind} must define string directory and pattern")
        else:
            directory = Path(spec["directory"])
            if directory.is_absolute() or ".." in directory.parts:
                errors.append(f"Manifest inventory.{kind}.directory must stay inside the repository")
        if kind in ("agents", "skills"):
            count = spec.get("minimum_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < HARD_MINIMUMS[kind]:
                errors.append(f"Manifest inventory.{kind}.minimum_count must be at least the hard floor {HARD_MINIMUMS[kind]}")
        else:
            required = spec.get("required")
            if not isinstance(required, list) or not all(isinstance(item, str) and item.strip() for item in required):
                errors.append(f"Manifest inventory.{kind}.required must be a list of non-empty filenames")
            elif len(required) != len(set(required)):
                errors.append(f"Manifest inventory.{kind}.required contains duplicate filenames")
            elif any(Path(item).name != item or item in {".", ".."} for item in required):
                errors.append(f"Manifest inventory.{kind}.required entries must be plain filenames")
    # CI supplies the target branch to prevent silent manifest shrinkage in a PR.
    base_ref = os.environ.get("MANIFEST_BASE_REF", "").strip()
    if base_ref:
        try:
            baseline_raw = subprocess.run(
                ["git", "show", f"{base_ref}:.claude/manifest.json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            ).stdout
            baseline = json.loads(baseline_raw)
            baseline_inventory = baseline.get("inventory", {})
            for kind, old_spec in baseline_inventory.items():
                new_spec = inventory.get(kind, {}) if isinstance(inventory, dict) else {}
                if kind in HARD_MINIMUMS:
                    old_min = old_spec.get("minimum_count", HARD_MINIMUMS[kind])
                    new_min = new_spec.get("minimum_count", 0)
                    if (
                        isinstance(old_min, int)
                        and not isinstance(old_min, bool)
                        and (not isinstance(new_min, int) or isinstance(new_min, bool) or new_min < old_min)
                    ):
                        errors.append(f"Manifest inventory.{kind}.minimum_count may not decrease from base ({old_min})")
                old_required = old_spec.get("required", [])
                new_required = new_spec.get("required", [])
                if isinstance(old_required, list) and isinstance(new_required, list):
                    removed = sorted(set(old_required) - set(new_required))
                    if removed:
                        errors.append(f"Manifest inventory.{kind}.required may not remove base entries: {', '.join(removed)}")
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
            errors.append(f"Cannot compare manifest with base ref {base_ref!r}: {exc}")
    return inventory


def read_text(path: Path) -> str:
    """Read UTF-8 text, recording failures rather than hiding them."""
    relative = path.relative_to(ROOT)
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"Cannot read {relative}: {exc}")
        return ""


def require_nonempty(path: Path, label: str | None = None) -> str:
    text = read_text(path) if path.is_file() else ""
    if not path.is_file():
        errors.append(f"Missing required {label or 'file'}: {path.relative_to(ROOT)}")
    elif not text.strip():
        errors.append(f"Empty required {label or 'file'}: {path.relative_to(ROOT)}")
    return text


manifest_inventory = load_manifest()


def inventory_paths(kind: str) -> list[Path]:
    spec = manifest_inventory.get(kind, {})
    directory = spec.get("directory")
    pattern = spec.get("pattern")
    if not isinstance(directory, str) or not isinstance(pattern, str):
        return []
    folder = ROOT / directory
    try:
        folder.resolve().relative_to(ROOT.resolve())
    except (OSError, ValueError):
        errors.append(f"Manifest inventory.{kind}.directory resolves outside the repository")
        return []
    return sorted(folder.glob(pattern)) if folder.is_dir() else []


agents = inventory_paths("agents")
skills = inventory_paths("skills")
commands = inventory_paths("commands")
templates = inventory_paths("templates")

for kind, paths in (("agents", agents), ("skills", skills)):
    spec = manifest_inventory.get(kind, {})
    minimum = spec.get("minimum_count")
    if isinstance(minimum, int) and not isinstance(minimum, bool) and len(paths) < minimum:
        errors.append(f"Manifest requires at least {minimum} {kind} files, found {len(paths)}")


def parse_frontmatter(path: Path, required_fields: tuple[str, ...] = ("name", "description")) -> dict[str, str]:
    text = require_nonempty(path)
    if not text:
        return {}
    if not text.startswith("---\n"):
        errors.append(f"Frontmatter must start with ---: {path.relative_to(ROOT)}")
        return {}
    match = re.search(r"\n---\s*(?:\n|$)", text[4:])
    if not match:
        errors.append(f"Frontmatter closing delimiter missing: {path.relative_to(ROOT)}")
        return {}
    block = text[4 : 4 + match.start()]
    fields: dict[str, str] = {}
    for line_number, line in enumerate(block.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"Invalid frontmatter line {line_number} in {path.relative_to(ROOT)}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            errors.append(f"Empty frontmatter key at line {line_number} in {path.relative_to(ROOT)}")
            continue
        if key in fields:
            errors.append(f"Duplicate frontmatter key '{key}' in {path.relative_to(ROOT)}")
        fields[key] = value
    for required in required_fields:
        if not fields.get(required, "").strip():
            errors.append(f"Missing or empty '{required}' in {path.relative_to(ROOT)}")
    return fields


def check_unique_names(paths: list[Path], kind: str) -> None:
    seen: dict[str, Path] = {}
    for path in paths:
        name = parse_frontmatter(path).get("name", "").strip()
        if not name:
            continue
        if name in seen:
            errors.append(f"Duplicate {kind} name '{name}': {seen[name].relative_to(ROOT)} and {path.relative_to(ROOT)}")
        else:
            seen[name] = path


def check_agent_tools(paths: list[Path]) -> None:
    for path in paths:
        raw = parse_frontmatter(path).get("tools", "").strip()
        if not raw:
            errors.append(f"Agent must declare an explicit 'tools' allowlist: {path.relative_to(ROOT)}")
            continue
        names = [tool.strip() for tool in raw.split(",") if tool.strip()]
        unknown = [tool for tool in names if tool not in ALLOWED_TOOLS]
        if unknown:
            errors.append(f"Unknown tools {unknown} in {path.relative_to(ROOT)}")
        if len(set(names)) != len(names):
            errors.append(f"Duplicate tools in {path.relative_to(ROOT)}")
        if path.stem in READ_ONLY_AGENTS and {"Edit", "Write", "Bash"} & set(names):
            errors.append(f"{path.stem} must remain read-only (no Edit/Write/Bash)")
        if "Agent" in names and path.stem != ORCHESTRATOR:
            errors.append(f"Only {ORCHESTRATOR} may delegate; remove 'Agent' from {path.relative_to(ROOT)}")
        if path.stem == ORCHESTRATOR and "Agent" not in names:
            errors.append(f"{ORCHESTRATOR} must list the 'Agent' tool to delegate")
        # Turn caps are the enforced stop condition for delegations (standards/sprint-sizing.md).
        turns = parse_frontmatter(path).get("maxTurns", "").strip()
        if path.stem != ORCHESTRATOR and not (turns.isdigit() and 5 <= int(turns) <= 100):
            errors.append(f"Agent must declare maxTurns between 5 and 100: {path.relative_to(ROOT)}")


check_agent_tools(agents)
check_unique_names(agents, "agent")
check_unique_names(skills, "skill")

# Cross-reference checks keep agent/skill wiring from silently drifting.
skill_paths = {path.resolve() for path in skills}
for path in agents:
    body = read_text(path)
    if "## Relevant skills" not in body:
        errors.append(f"Agent is missing a Relevant skills section: {path.relative_to(ROOT)}")
    for reference in re.findall(r"`(\.claude/skills/[^\`]+/SKILL\.md)`", body):
        target = (ROOT / reference).resolve()
        if target not in skill_paths or not target.is_file():
            errors.append(f"Agent references a missing skill '{reference}': {path.relative_to(ROOT)}")

claude_instructions = read_text(ROOT / ".claude" / "CLAUDE.md")
for path in skills:
    reference = path.relative_to(ROOT).as_posix()
    if reference not in claude_instructions:
        errors.append(f"Shared skill is missing from the skill routing index: {reference}")

for path in agents:
    body = read_text(path).split("---", 2)
    if len(body) < 3 or len(body[2].strip()) < 80:
        errors.append(f"Agent body is missing or suspiciously short: {path.relative_to(ROOT)}")

for path in skills:
    text = require_nonempty(path, "skill")
    if len(text.splitlines()) < 8:
        errors.append(f"Skill content is suspiciously short: {path.relative_to(ROOT)}")
    for section in ("## When to use", "## Required inputs", "## Procedure", "## Expected outputs", "## Quality checks"):
        if section not in text:
            errors.append(f"Skill is missing the '{section[3:]}' section: {path.relative_to(ROOT)}")
    description = parse_frontmatter(path).get("description", "").strip()
    if len(description) < 20 or description.casefold() in {"skill", "todo", "tbd", "x"}:
        errors.append(f"Skill description is missing or too generic: {path.relative_to(ROOT)}")


def check_required_files(kind: str, paths: list[Path]) -> None:
    spec = manifest_inventory.get(kind, {})
    required = spec.get("required", [])
    actual = {path.name for path in paths}
    for name in sorted(set(required) - actual):
        errors.append(f"Missing required {kind[:-1] if kind.endswith('s') else kind}: {spec.get('directory', kind)}/{name}")


check_required_files("agents", agents)
check_required_files("commands", commands)
for path in commands:
    text = require_nonempty(path, "command")
    parse_frontmatter(path, required_fields=("description",))
    if len(text.splitlines()) < 5:
        errors.append(f"Command content is suspiciously short: {path.relative_to(ROOT)}")

check_required_files("templates", templates)
for path in templates:
    require_nonempty(path, "template")

required_files = [
    "README.md",
    ".claude/CLAUDE.md",
    "workflows/future-project-workflow.md",
    "workflows/project-bootstrap.md",
    "workflows/agile-agent-delivery.md",
    "workflows/orchestration-contract.md",
    "workflows/sprint-governance.md",
    "workflows/backlog-quality-gates.md",
    "standards/agent-contract.md",
    "docs/orchestration-design.md",
    "docs/agent-traceability.md",
    "docs/verification-report.md",
    "docs/agile-command-reference.md",
    "standards/engineering-principles.md",
    "standards/security-principles.md",
    "standards/git-workflow.md",
    "standards/definition-of-done.md",
    "standards/telemetry.md",
    "standards/human-in-the-loop.md",
    "standards/validation-gates.md",
    "templates/spec-ears.md",
    "standards/agent-isolation.md",
    "standards/license-risk.md",
    "standards/ci-cd-hardening.md",
    "standards/model-agnosticism.md",
    "adapters/README.md",
    "adapters/claude-code/README.md",
    "docs/portability-audit.md",
    "scripts/new_worktree.sh",
    "scripts/cleanup_worktree.sh",
    "tests/test_worktree.sh",
    "scripts/roi_report.py",
    "scripts/check_licenses.py",
    "tests/test_license_check.py",
    ".claude/metrics/README.md",
    "tests/test_roi_report.py",
]
for relative in required_files:
    require_nonempty(ROOT / relative)

# Shared agent Markdown must not embed undocumented Claude Code runtime markers.
model_agnosticism_path = ROOT / "standards" / "model-agnosticism.md"
model_agnosticism_text = require_nonempty(model_agnosticism_path, "model agnosticism standard")
for marker in ("$ARGUMENTS", "$CLAUDE_[A-Z0-9_]+", "<tool-name>", "<command-name>"):
    if marker not in model_agnosticism_text:
        errors.append(f"Model agnosticism standard must document prohibited pattern: {marker}")
agent_forbidden_patterns = (
    (re.compile(r"\$ARGUMENTS"), "$ARGUMENTS"),
    (re.compile(r"\$CLAUDE_[A-Z0-9_]+"), "$CLAUDE_[A-Z0-9_]+"),
    (re.compile(r"<tool-name>|<command-name>"), "Claude Code transcript/tool control marker"),
)
for agent_path in agents:
    agent_text = read_text(agent_path)
    for line_number, line in enumerate(agent_text.splitlines(), start=1):
        for pattern, label in agent_forbidden_patterns:
            if pattern.search(line):
                errors.append(
                    f"Undocumented Claude Code-specific pattern {label!r} in "
                    f"{agent_path.relative_to(ROOT)}:{line_number}"
                )

hitl_path = ROOT / "standards" / "human-in-the-loop.md"
hitl_text = require_nonempty(hitl_path, "HITL standard")
if hitl_text:
    for checkpoint in ("CP1", "CP2", "CP3", "CP4"):
        if checkpoint not in hitl_text:
            errors.append(f"HITL standard is missing required checkpoint: {checkpoint}")

contract_path = ROOT / "workflows" / "orchestration-contract.md"
if contract_path.is_file():
    contract = read_text(contract_path)
    for marker in (
        "Session-start / resume protocol",
        "Task ownership and concurrency",
        "Retry, failure and recovery",
        "Quality and merge gate",
        "Daily report evidence rules",
        "human repository owner merges PRs",
        "atomic exclusivity",
        "Authority and precedence",
    ):
        if marker.casefold() not in contract.casefold():
            errors.append(f"Orchestration contract missing required marker: {marker}")

design_path = ROOT / "docs" / "orchestration-design.md"
if design_path.is_file():
    design = read_text(design_path)
    if "only after the user approves a real project" in design.casefold():
        errors.append("Contradictory activation rule in docs/orchestration-design.md")

settings_path = ROOT / ".claude" / "settings.json"
settings_text = require_nonempty(settings_path, "Claude Code permission settings")
if settings_text:
    try:
        settings = json.loads(settings_text)
        deny = settings.get("permissions", {}).get("deny", [])
        required_denies = (
            "Bash(git push --force*)",
            "Bash(git push -f*)",
            "Bash(git push origin main*)",
            "Bash(git push origin HEAD:main*)",
            "Bash(git reset --hard*)",
            "Bash(git clean*)",
            "Bash(gh repo delete*)",
            "Bash(gh pr merge*)",
            "Bash(rm -rf*)",
            "Bash(gh repo create*)",
            "Bash(terraform apply*)",
            "Bash(terraform destroy*)",
            "Bash(kubectl apply*)",
            "Bash(kubectl delete*)",
            "Bash(docker push*)",
            "Bash(cat .env*)",
            "Bash(cat */.env*)",
            "Read(./.env)",
            "Read(./.env.*)",
            "Read(./**/*.pem)",
            "Read(./**/*.key)",
        )
        required_denies += (
            "Bash(git push*--force*)",
            "Bash(git push* -f*)",
            "Bash(git push* +*)",
            "Bash(git push* main)",
            "Bash(git push* main *)",
            "Bash(git push*:main)",
            "Bash(git push*:refs/heads/main*)",
            "Bash(git push*--delete*)",
            "Bash(git push*--mirror*)",
            "Bash(rm -fr*)",
            "Bash(rm -Rf*)",
            "Bash(rm --recursive*)",
            "Bash(gh auth token*)",
            "Bash(gh auth status*--show-token*)",
            "Bash(printenv*)",
            "Bash(source .env*)",
            "Bash(head*.env*)",
            "Bash(tail*.env*)",
            "Bash(grep*.env*)",
            "Bash(sed*.env*)",
            "Bash(awk*.env*)",
            "Read(./secrets/**)",
            "Edit(./.env)",
            "Edit(./.env.*)",
            "Edit(./**/*.pem)",
            "Edit(./**/*.key)",
            "Edit(./secrets/**)",
            "mcp__github__merge_pull_request",
            "mcp__github__enable_pr_auto_merge",
        )
        required_asks = (
            "Bash(git push*)",
            "Bash(rm -r*)",
            "Bash(rm -R*)",
            "Bash(gh api*)",
            "Bash(gh repo edit*)",
            "Bash(gh secret*)",
            "Edit(./.claude/settings.json)",
            "Edit(./.github/workflows/**)",
            "Edit(./.github/CODEOWNERS)",
            "Edit(./.github/dependabot.yml)",
            "Edit(./.claude/CLAUDE.md)",
            "Edit(./.claude/manifest.json)",
            "Bash(*provision_project.py apply*)",
        )
        permissions = settings.get("permissions", {})
        ask = permissions.get("ask", [])
        allow = permissions.get("allow", [])
        for name, rules in (("deny", deny), ("ask", ask), ("allow", allow)):
            if not isinstance(rules, list) or not all(isinstance(rule, str) for rule in rules):
                errors.append(f"Claude Code permission {name} rules must be a list of strings")
            elif len(set(rules)) != len(rules):
                errors.append(f"Claude Code permission {name} rules contain duplicates")
        if isinstance(deny, list) and isinstance(ask, list) and isinstance(allow, list):
            for rule in required_denies:
                if rule not in deny:
                    errors.append(f"Claude Code permission deny rule missing: {rule}")
            for rule in required_asks:
                if rule not in ask:
                    errors.append(f"Claude Code permission ask rule missing: {rule}")
            # Claude Code 2.1.303 warns that Write(path) rules are never matched; Edit(path) covers all file edits.
            for rule in deny + ask + allow:
                if isinstance(rule, str) and rule.startswith("Write(") and rule != "Write(*)":
                    errors.append(f"Use Edit(...) instead of ineffective path rule {rule}")
            unrestricted = {"*", "Bash", "Bash(*)", "Edit", "Edit(*)", "Write", "Write(*)", "Read", "Read(*)"}
            for rule in allow:
                if isinstance(rule, str) and rule.strip() in unrestricted:
                    errors.append(f"Claude Code permission allow rule is unrestricted: {rule}")
                if rule in deny or rule in ask:
                    errors.append(f"Claude Code permission rule is both allowed and denied/asked: {rule}")
    except (json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"Invalid .claude/settings.json: {exc}")

ignore_path = ROOT / ".gitignore"
ignore_text = require_nonempty(ignore_path, ".gitignore")
for pattern in (".env", "*.pem", "*.key"):
    if pattern not in ignore_text:
        errors.append(f".gitignore missing sensitive-file pattern: {pattern}")

workflow_path = ROOT / ".github" / "workflows" / "validate-team.yml"
workflow_text = require_nonempty(workflow_path, "validation workflow")
if workflow_text:
    if not re.search(r"(?m)^\s*contents:\s*read\s*$", workflow_text):
        errors.append("Validation workflow must keep contents permission read-only")
    if "persist-credentials: false" not in workflow_text:
        errors.append("Validation workflow checkout must set persist-credentials: false")
    if re.search(r"(?m)^\s*uses:\s*[^\n]+@(?:v?\d+(?:\.\d+){0,2}|main|master)\s*(?:#.*)?$", workflow_text):
        errors.append("Validation workflow must pin actions to full commit SHAs")

# Every workflow must declare least-privilege token permissions; write-all is prohibited.
workflow_dir = ROOT / ".github" / "workflows"
for candidate in sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml")):
    workflow = require_nonempty(candidate, "GitHub Actions workflow")
    if not workflow:
        continue
    if re.search(r"(?im)^\s*permissions\s*:\s*write-all\s*$", workflow):
        errors.append(f"Workflow must not use permissions: write-all: {candidate.relative_to(ROOT)}")
    if not re.search(r"(?m)^permissions:\s*\n(?:^[ \t]+[^\n]+\n?)+", workflow):
        errors.append(f"Workflow must declare explicit least-privilege permissions: {candidate.relative_to(ROOT)}")

license_workflow = ROOT / ".github" / "workflows" / "license-check.yml"
license_workflow_text = require_nonempty(license_workflow, "dependency license workflow")
if license_workflow_text:
    if not re.search(r"(?m)^\s*contents:\s*read\s*$", license_workflow_text):
        errors.append("License check workflow must keep contents permission read-only")
    if not re.search(r"(?m)^\s*push\s*:", license_workflow_text) or not re.search(
        r"(?m)^\s*pull_request\s*:", license_workflow_text
    ):
        errors.append("License check workflow must run on push and pull_request")
    if "scripts/check_licenses.py" not in license_workflow_text:
        errors.append("License check workflow must run scripts/check_licenses.py")

secret_workflow = ROOT / ".github" / "workflows" / "secret-scan.yml"
secret_text = require_nonempty(secret_workflow, "secret scanning workflow")
if secret_text:
    if "gitleaks" not in secret_text.casefold() or "pull_request:" not in secret_text:
        errors.append("Secret scanning workflow must run Gitleaks on pull requests")
    if not re.search(r"(?m)^\s*contents:\s*read\s*$", secret_text):
        errors.append("Secret scanning workflow must keep contents permission read-only")
    if "persist-credentials: false" not in secret_text:
        errors.append("Secret scanning workflow checkout must set persist-credentials: false")
    if re.search(r"(?m)^\s*uses:\s*[^\n]+@(?:v?\d+(?:\.\d+){0,2}|main|master)\s*(?:#.*)?$", secret_text):
        errors.append("Secret scanning workflow must pin actions to full commit SHAs")

dependabot_path = ROOT / ".github" / "dependabot.yml"
dependabot_text = require_nonempty(dependabot_path, "Dependabot configuration")
if dependabot_text and ("package-ecosystem: github-actions" not in dependabot_text or "interval: weekly" not in dependabot_text):
    errors.append("Dependabot must schedule weekly GitHub Actions updates")

print(
    f"Agents: {len(agents)} discovered; manifest minimum {manifest_inventory.get('agents', {}).get('minimum_count', 'invalid')}"
)
print(
    f"Skills: {len(skills)} discovered; manifest minimum {manifest_inventory.get('skills', {}).get('minimum_count', 'invalid')}"
)
print(
    f"Commands: {len(commands)} discovered; {len(manifest_inventory.get('commands', {}).get('required', []))} required by manifest"
)
print(
    f"Templates: {len(templates)} discovered; {len(manifest_inventory.get('templates', {}).get('required', []))} required by manifest"
)
print(f"Required documentation files checked: {len(required_files)}")
print("Security checks: Claude deny rules, .gitignore, read-only CI, checkout credentials, Gitleaks and Dependabot")
for script_name in ("new_worktree.sh", "cleanup_worktree.sh"):
    script_path = ROOT / "scripts" / script_name
    if script_path.is_file() and not (script_path.stat().st_mode & 0o111):
        errors.append(f"Worktree script must be executable: scripts/{script_name}")
print("Static-only validation: does not prove Claude Code runtime behavior or GitHub owner settings")

if errors:
    print("FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("PASS")
