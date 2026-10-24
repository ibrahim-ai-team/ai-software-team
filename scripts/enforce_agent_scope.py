#!/usr/bin/env python3
"""Fail-closed, read-only preflight for agent file scopes (Python 3.10+, stdlib)."""
import argparse
import fnmatch
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".claude" / "agent-scopes.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    path = args.path
    if path == "":
        print("DENY: path must not be empty", file=sys.stderr)
        return 2
    pure = PurePosixPath(path)
    if pure.is_absolute() or path.startswith("/") or "\\\\" in path or ".." in pure.parts or (len(path) >= 2 and path[1] == ":"):
        print(f"DENY: unsafe repository-relative path: {path}", file=sys.stderr)
        return 1
    normalized = pure.as_posix()
    if normalized in {"", "."}:
        print("DENY: path must not be empty", file=sys.stderr)
        return 2
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"DENY: cannot load scope configuration: {exc}", file=sys.stderr)
        return 1
    if not isinstance(config, dict) or args.agent not in config:
        print(f"DENY: unknown agent: {args.agent}", file=sys.stderr)
        return 1
    scope = config[args.agent]
    if not isinstance(scope, dict):
        print(f"DENY: invalid scope for agent: {args.agent}", file=sys.stderr)
        return 1
    allowed, forbidden = scope.get("allowed_paths"), scope.get("forbidden_paths")
    if not isinstance(allowed, list) or not all(isinstance(p, str) for p in allowed):
        print(f"DENY: invalid allowed_paths for agent: {args.agent}", file=sys.stderr)
        return 1
    if not isinstance(forbidden, list) or not all(isinstance(p, str) for p in forbidden):
        print(f"DENY: invalid forbidden_paths for agent: {args.agent}", file=sys.stderr)
        return 1
    if any(fnmatch.fnmatchcase(normalized, p) for p in forbidden):
        print(f"DENY: refused_path={normalized}; matched forbidden scope", file=sys.stderr)
        return 1
    if not any(fnmatch.fnmatchcase(normalized, p) for p in allowed):
        print(f"DENY: refused_path={normalized}; no allowed scope matched", file=sys.stderr)
        return 1
    print(f"ALLOW: agent={args.agent} path={normalized}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
