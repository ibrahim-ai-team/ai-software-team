#!/usr/bin/env python3
"""Claude Code PreToolUse hook for enforcing agent write scopes and recording denials.

This hook protects direct file-editing tools. It is not an OS sandbox: arbitrary
shell commands and external tools must be separately restricted for full isolation.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "enforce_agent_scope.py"
TELEMETRY = ROOT / "scripts" / "append_telemetry.py"
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}


def deny(reason: str, agent: str, path: str) -> int:
    # Never include file contents or other potentially sensitive data in telemetry.
    details = json.dumps({"refused_path": path, "reason": reason}, separators=(",", ":"))
    subprocess.run(
        [sys.executable, str(TELEMETRY), "--agent", agent, "--action", "error",
         "--story", "SCOPE-ENFORCEMENT", "--details", details],
        cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, check=False,
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Agent scope denied write: {reason}",
        }
    }))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError):
        print("Invalid PreToolUse JSON payload; refusing write.", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("Invalid PreToolUse payload; refusing write.", file=sys.stderr)
        return 2
    tool = payload.get("tool_name")
    if tool not in WRITE_TOOLS:
        return 0

    # Claude Code supplies agent_type for subagent calls / sessions launched with --agent.
    agent = payload.get("agent_type")
    tool_input = payload.get("tool_input")
    path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(path, str) or not path.strip():
        return deny("missing or invalid file_path", agent if isinstance(agent, str) and agent else "unknown-agent", str(path or ""))

    # Main-session writes are not scoped by this agent-specific policy.
    # Subagent identities must be known and configured; unknown agents fail closed.
    if not isinstance(agent, str) or not agent.strip():
        return 0
    if not isinstance(tool_input, dict):
        return deny("invalid tool input", agent, path)

    candidate = Path(path)
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()
        relative = resolved.relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return deny("path escapes repository root", agent, path)

    result = subprocess.run(
        [sys.executable, str(CHECKER), "--agent", agent, "--path", relative],
        cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        reason = result.stderr.strip() or result.stdout.strip() or "scope checker failed"
        return deny(reason, agent, relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
