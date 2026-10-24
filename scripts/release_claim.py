#!/usr/bin/env python3
"""Release refs/claims/<task-id> on a Git remote."""

import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--remote", default="origin")
    args = parser.parse_args()
    ref = f"refs/claims/{args.task_id}"
    check = subprocess.run(["git", "check-ref-format", ref], capture_output=True, text=True)
    if check.returncode or "/" in args.task_id:
        print(f"Invalid task ID for a Git ref: {args.task_id}", file=sys.stderr)
        return 2
    result = subprocess.run(
        ["git", "push", args.remote, f":{ref}"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print(result.stderr.strip() or "Git push failed.", file=sys.stderr)
        return 3
    print(f"Claim released (or already absent): {args.task_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
