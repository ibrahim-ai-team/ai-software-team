"""Claude Code PreToolUse hook for enforcing agent write scopes and recording denials.

Bash is deliberately restricted to a small read/test command allowlist. Shell
syntax and commands capable of writing files are denied; this hook is a
guardrail, not an OS sandbox.
"""

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "enforce_agent_scope.py"
TELEMETRY = ROOT / "scripts" / "append_telemetry.py"
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
SAFE_SIMPLE_COMMANDS = {"pytest", "ls", "cat", "grep", "find", "wc", "head", "tail"}
SHELL_META = re.compile(r"[<>|;&`]|\$\(|\n|\r")
REDIRECTION_TARGET = re.compile(r"(?:>>?|[0-9]+>>?)\s*([^\s;&|<>]+)")
WRITE_COMMANDS = {"tee", "cp", "mv", "rm", "dd"}


def deny(reason: str, agent: str, path: str = "") -> int:
    # Never include file contents or other potentially sensitive data in telemetry.
    details = json.dumps({"refused_path": path, "reason": reason}, separators=(",", ":"))
    subprocess.run(
        [
            sys.executable,
            str(TELEMETRY),
            "--agent",
            agent,
            "--action",
            "error",
            "--story",
            "SCOPE-ENFORCEMENT",
            "--details",
            details,
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Agent scope denied: {reason}",
                }
            }
        )
    )
    return 0


def _scope_check_target(agent: str, target: str) -> tuple[bool, str]:
    """Check a shell write target with the same path checker used by file tools."""
    candidate = Path(target)
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()
        relative = resolved.relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return False, target
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--agent", agent, "--path", relative],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0, relative


def _bash_decision(command: object, agent: str) -> tuple[bool, str, str]:
    if not isinstance(command, str) or not command.strip():
        return False, "missing or invalid Bash command", ""
    # Extract common output redirection targets before rejecting shell syntax so
    # a subagent's target is still checked against its configured file scope.
    for match in REDIRECTION_TARGET.finditer(command):
        target = match.group(1).strip("'\\\"")
        if agent != "unknown-agent":
            allowed, relative = _scope_check_target(agent, target)
            if not allowed:
                return False, "redirection target outside agent scope", relative
        return False, "shell redirection is not allowed", target
    if SHELL_META.search(command):
        return False, "ambiguous shell syntax (pipes, chaining, subshells, or redirection)", ""
    try:
        args = shlex.split(command, posix=True)
    except ValueError:
        return False, "malformed shell quoting", ""
    if not args:
        return False, "empty Bash command", ""
    executable = Path(args[0]).name
    if executable == "git" and len(args) >= 2 and args[1] in {"status", "diff", "log"}:
        return True, "", ""
    if executable == "ruff" and len(args) >= 2 and args[1] == "check":
        return True, "", ""
    if executable == "gitleaks" and len(args) >= 2 and args[1] == "detect":
        return True, "", ""
    if executable in SAFE_SIMPLE_COMMANDS:
        if executable == "find" and any(arg in {"-exec", "-execdir", "-delete"} for arg in args):
            return False, "unsafe find option", ""
        return True, "", ""
    if executable == "sed" and any(arg == "-i" or arg.startswith("-i") for arg in args[1:]):
        return False, "in-place sed edits are not allowed", args[-1] if len(args) > 1 else ""
    if executable in WRITE_COMMANDS:
        target = args[-1] if len(args) > 1 else ""
        if target and agent != "unknown-agent":
            allowed, relative = _scope_check_target(agent, target)
            if not allowed:
                return False, f"{executable} target outside agent scope", relative
        return False, f"{executable} can modify files and is not allowed", target
    return False, f"command not on safe allowlist: {executable}", ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError):
        print("Invalid PreToolUse JSON payload; refusing tool call.", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("Invalid PreToolUse payload; refusing tool call.", file=sys.stderr)
        return 2
    tool = payload.get("tool_name")
    if tool == "Bash":
        agent_value = payload.get("agent_type")
        agent = agent_value.strip() if isinstance(agent_value, str) and agent_value.strip() else "unknown-agent"
        tool_input = payload.get("tool_input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        allowed, reason, path = _bash_decision(command, agent)
        if allowed:
            return 0
        return deny(reason, agent, path)
    if tool not in WRITE_TOOLS:
        return 0

    # Claude Code supplies agent_type for subagent calls / sessions launched with --agent.
    agent = payload.get("agent_type")
    tool_input = payload.get("tool_input")
    path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(path, str) or not path.strip():
        identity = agent if isinstance(agent, str) and agent else "unknown-agent"
        return deny("missing or invalid file_path", identity, str(path or ""))

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
        [
            sys.executable,
            str(CHECKER),
            "--agent",
            agent,
            "--path",
            relative,
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        reason = result.stderr.strip() or result.stdout.strip() or "scope checker failed"
        return deny(reason, agent, relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
