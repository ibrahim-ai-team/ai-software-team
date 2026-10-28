"""Report every changed file that falls outside an agent's write scope (read-only).

Collects committed, staged, unstaged, untracked and deleted changes in a repository or worktree
against a base ref, and checks each path with scripts/enforce_agent_scope.py, the same checker the
runtime hook uses. Exit 0: all in scope; 1: at least one path out of scope; 2: invalid input or git error.
Deciding whether to reject or isolate an out-of-scope edit stays with the orchestrator.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "enforce_agent_scope.py"
REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")


def git(repo: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return [line for line in result.stdout.splitlines() if line.strip()]


def changed_paths(repo: Path, base: str) -> list[str]:
    """Every path changed since base: committed, staged, unstaged and untracked, including deletions."""
    paths: set[str] = set()
    paths.update(git(repo, "diff", "--name-only", "--no-renames", f"{base}...HEAD"))
    paths.update(git(repo, "diff", "--name-only", "--no-renames", "--cached"))
    paths.update(git(repo, "diff", "--name-only", "--no-renames"))
    paths.update(git(repo, "ls-files", "--others", "--exclude-standard"))
    return sorted(paths)


def check_scope(agent: str, path: str) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--agent", agent, "--path", path],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    message = (result.stderr or result.stdout).strip()
    return result.returncode == 0, message


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True, help="agent whose scope applies, e.g. backend-developer")
    parser.add_argument("--base", default="main", help="base ref the delegation branched from (default: main)")
    parser.add_argument("--repo", default=".", help="repository or worktree to inspect (default: current directory)")
    args = parser.parse_args(argv)
    if not REF_PATTERN.fullmatch(args.base) or ".." in args.base:
        print("ERROR: --base must be a plain branch, tag or commit name", file=sys.stderr)
        return 2
    try:
        paths = changed_paths(Path(args.repo), args.base)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not paths:
        print(f"No changes against {args.base}.")
        return 0
    outside = 0
    for path in paths:
        allowed, message = check_scope(args.agent, path)
        if allowed:
            print(f"IN_SCOPE {path}")
        else:
            outside += 1
            print(f"OUT_OF_SCOPE {path}: {message}")
    print(f"{len(paths)} changed path(s), {outside} outside the scope of {args.agent}.")
    return 1 if outside else 0


if __name__ == "__main__":
    raise SystemExit(main())
