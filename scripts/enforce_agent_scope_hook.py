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
# Options that make an otherwise read-only allowed command write files or run other commands.
UNSAFE_OPTIONS = {
    "git": ("--output", "--ext-diff", "--textconv"),
    "ruff": ("--fix", "--fix-only", "--unsafe-fixes", "--add-noqa", "--output-file", "-o", "--watch", "-w"),
    "gitleaks": ("--report-path", "-r"),
    "find": ("-exec", "-execdir", "-delete", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls"),
}
# Governance scripts the orchestration contract requires. Patterns are matched against the raw command
# string, not shlex tokens: bash applies brace, glob, `$` and `~` expansion to what it runs, so they admit
# none of those characters (except the fixed `docs/sprints/*.md` glob).
COORDINATORS = frozenset({"agile-orchestrator", "unknown-agent"})  # unknown-agent: the main session without --agent
_ID = r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}"
_PATH = r"(?:[A-Za-z0-9_][A-Za-z0-9._-]*/)*[A-Za-z0-9_][A-Za-z0-9._-]*"
_TEXT = r"'[^']{1,500}'"  # single-quoted, so bash performs no expansion inside
_GOVERNANCE_ROLES = COORDINATORS | {"project-manager", "release-manager"}
_STATUS_FLAGS = r"(?: --json| --health-json| --strict| --filter (?:agent|task)=[A-Za-z0-9._-]+)*"
# (agents allowed to run it, or None for any agent; script name and arguments after `scripts/`)
ALLOWED_SCRIPTS = (
    (None, rf"relevant_lessons\.py --story {_ID}(?: --max [0-9]{{1,4}})?"),
    (COORDINATORS, rf"detect_conflict\.py --story {_ID} --agents [a-z0-9-]+(?:,[a-z0-9-]+)*"),
    (COORDINATORS, rf"check_approvals\.py --story {_ID} --checkpoint CP[1-4]"),
    (COORDINATORS, rf"check_gates\.py --story {_ID} --gate G[12](?: --commit [0-9a-fA-F]{{40}})?"),
    (COORDINATORS, rf"check_claims\.py {_PATH}"),
    (COORDINATORS, rf"enforce_agent_scope\.py --agent [a-z0-9-]+ --path {_PATH}"),
    (
        COORDINATORS,
        rf"check_diff_scope\.py --agent [a-z0-9-]+(?: --base [A-Za-z0-9][A-Za-z0-9._/-]{{0,199}})?"
        rf"(?: --repo (?:\.\./worktrees/{_ID}|{_PATH}))?",
    ),
    (COORDINATORS, r"coordinator_lock\.py (?:acquire(?: --ttl [0-9]{1,6})?|status|release)"),
    (COORDINATORS, rf"add_lesson\.py --title {_TEXT} --context {_TEXT} --error {_TEXT} --rule {_TEXT} --story {_ID}"),
    (COORDINATORS | {"project-manager"}, rf"status_report\.py{_STATUS_FLAGS}"),
    (COORDINATORS | {"ci-verifier"}, rf"detect_checks\.py(?: --repo (?:\.\./worktrees/{_ID}|{_PATH}))?"),
    (
        COORDINATORS,
        r"route_model\.py --agent [a-z0-9-]+ --skill [a-z0-9-]+ --size (?:XS|S|M|L|XL)"
        r"(?: --risk)?(?: --retry)?(?: --no-production-code)?",
    ),
    (_GOVERNANCE_ROLES, rf"check_governance\.py(?: (?:{_PATH}|docs/sprints/\*\.md))+"),
    (_GOVERNANCE_ROLES, rf"check_governance\.py --frontend-readiness --design-handoff {_PATH}"),
    (_GOVERNANCE_ROLES, rf"check_governance\.py --state {_PATH} --repo \. --release"),
    # A real apply also needs the settings `ask` prompt and the human PROVISION-<id> approval record.
    (COORDINATORS, rf"provision_project\.py plan (?:\.provisioning/)?{_PATH}(?: --check-github)?"),
    (COORDINATORS, rf"provision_project\.py apply (?:\.provisioning/)?{_PATH}(?: --dry-run)?"),
)
# Worktree creation only; cleanup deletes work and stays a human-run command.
WORKTREE_CREATE = re.compile(rf"\./scripts/new_worktree\.sh {_ID} {_ID}")
# ci-verifier's closed command allowlist (.claude/agents/ci-verifier.md), for that role only. Running a test
# suite executes repository code by design; arguments stay plain words with no shell-expansion characters.
CI_VERIFIER_CHECKS = re.compile(
    rf"python3? -m (?:pytest|unittest)(?: [A-Za-z0-9_./:-]+)*"
    rf"|ruff format --check(?: {_PATH})*"
    r"|npm (?:test|run lint|run build)"
    r"|make (?:test|lint)"
)


def _in_repository_root(cwd: object) -> bool:
    # Bash resolves a relative path against its own working directory, so relative forms require ROOT.
    if not isinstance(cwd, str):
        return False
    try:
        return Path(cwd).resolve() == ROOT.resolve()
    except OSError:
        return False


def _is_allowed_script(command: str, cwd: object, agent: str) -> bool:
    """Allow only the exact governance-script invocations in ALLOWED_SCRIPTS, for the listed agents."""
    in_root = _in_repository_root(cwd)
    if agent in COORDINATORS and in_root and WORKTREE_CREATE.fullmatch(command):
        return True
    scripts_dir = re.escape((ROOT / "scripts").as_posix())
    for agents, body in ALLOWED_SCRIPTS:
        if agents is not None and agent not in agents:
            continue
        if re.fullmatch(rf"python3? {scripts_dir}/{body}", command):
            return True
        if in_root and re.fullmatch(rf"python3? scripts/{body}", command):
            return True
    return False


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


def _has_unsafe_option(executable: str, args: list[str]) -> bool:
    for option in UNSAFE_OPTIONS.get(executable, ()):
        for arg in args[1:]:
            if arg == option or arg.startswith(option + "="):
                return True
            # Short options can carry their value attached, as in `-ofile`.
            if len(option) == 2 and option[1] != "-" and arg.startswith(option):
                return True
    return False


# Specialists may read only the repository and the per-story worktrees (standards/agent-isolation.md).
WORKTREES_DIR = ROOT.parent / "worktrees"
READ_TOOLS = {"Read", "Grep", "Glob"}
READ_COMMANDS = {"ls", "cat", "grep", "find", "wc", "head", "tail", "git"}
# `$` and braces always expand; `~` only at a word start or after `=`/`:` (so `HEAD~3` stays allowed).
EXPANSION_CHARS = re.compile(r"[${}]|(?:^|[=:])~")


def _allowed_read_roots() -> tuple[Path, ...]:
    return ROOT.resolve(), WORKTREES_DIR.resolve()


def _inside_read_roots(path_text: str, base: Path) -> bool:
    candidate = Path(path_text)
    try:
        resolved = (candidate if candidate.is_absolute() else base / candidate).resolve()
    except OSError:
        return False
    return any(resolved == root or root in resolved.parents for root in _allowed_read_roots())


def _base_dir(cwd: object) -> Path:
    return Path(cwd) if isinstance(cwd, str) and cwd else ROOT


def _read_scope_problem(executable: str, args: list[str], cwd: object) -> str | None:
    """Why a specialist's read command reaches outside the repository and worktrees, or None."""
    base = _base_dir(cwd)
    if not _inside_read_roots(str(base), ROOT):
        return "working directory is outside the repository"
    if executable == "git" and "--no-index" in args:
        return "git --no-index can read files outside the repository"
    for arg in args[1:]:
        # Bash expands these before the command runs, so the hook cannot see the real path.
        if EXPANSION_CHARS.search(arg):
            return "shell expansion characters in a read command"
        value = arg
        if arg.startswith("-"):
            if "=" in arg:
                value = arg.split("=", 1)[1]
            elif "/" in arg:
                value = arg[arg.index("/") :]  # attached short-option value, as in -f/etc/passwd
            else:
                continue
        if ("/" in value or value.startswith(".")) and not _inside_read_roots(value, base):
            return f"path outside the repository: {value}"
    return None


def _read_tool_problem(tool: str, tool_input: object, cwd: object) -> str | None:
    """Why a specialist's Read, Grep or Glob call reaches outside the repository and worktrees, or None."""
    if not isinstance(tool_input, dict):
        return "invalid tool input"
    base = _base_dir(cwd)
    candidates = [tool_input.get("file_path"), tool_input.get("path")]
    pattern = tool_input.get("pattern")
    if tool == "Glob" and isinstance(pattern, str) and (pattern.startswith(("/", "~")) or ".." in pattern):
        candidates.append(pattern)
    for value in candidates:
        if isinstance(value, str) and value and (value.startswith("~") or not _inside_read_roots(value, base)):
            return f"path outside the repository: {value}"
    return None


def _scope_relative(resolved: Path, agent: str) -> str | None:
    """A write target relative to the repository, or to one of this agent's own worktrees, else None."""
    root = ROOT.resolve()
    if resolved == root or root in resolved.parents:
        return resolved.relative_to(root).as_posix()
    worktrees = WORKTREES_DIR.resolve()
    if worktrees in resolved.parents:
        parts = resolved.relative_to(worktrees).parts
        # new_worktree.sh names them wt-<agent>-<story>; another agent's worktree is never in scope.
        if len(parts) >= 2 and parts[0].startswith(f"wt-{agent}-"):
            return Path(*parts[1:]).as_posix()
    return None


def _bash_decision(command: object, agent: str, cwd: object = None) -> tuple[bool, str, str]:
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
    if _is_allowed_script(command, cwd, agent):
        return True, "", ""
    if agent == "ci-verifier" and CI_VERIFIER_CHECKS.fullmatch(command):
        return True, "", ""
    # A bare command name only: a path such as `./git` or `/tmp/x/ls` could run any binary.
    if "/" in args[0]:
        return False, "commands must be invoked by bare name", ""
    executable = args[0]
    if _has_unsafe_option(executable, args):
        return False, f"unsafe {executable} option", ""
    if agent not in COORDINATORS and executable in READ_COMMANDS and (problem := _read_scope_problem(executable, args, cwd)):
        return False, problem, ""
    if executable == "git" and len(args) >= 2 and args[1] in {"status", "diff", "log"}:
        return True, "", ""
    if executable == "ruff" and len(args) >= 2 and args[1] == "check":
        return True, "", ""
    if executable == "gitleaks" and len(args) >= 2 and args[1] == "detect":
        return True, "", ""
    if executable in SAFE_SIMPLE_COMMANDS:
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
        allowed, reason, path = _bash_decision(command, agent, payload.get("cwd"))
        if allowed:
            return 0
        return deny(reason, agent, path)
    if tool in READ_TOOLS:
        agent_value = payload.get("agent_type")
        agent = agent_value.strip() if isinstance(agent_value, str) and agent_value.strip() else "unknown-agent"
        if agent in COORDINATORS:
            return 0
        problem = _read_tool_problem(tool, payload.get("tool_input"), payload.get("cwd"))
        return deny(problem, agent) if problem else 0
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
    except OSError:
        return deny("path escapes repository root", agent, path)
    relative = _scope_relative(resolved, agent)
    if relative is None:
        return deny("path is outside the repository and this agent's worktrees", agent, path)

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
