#!/usr/bin/env python3
"""Release refs/claims/<task-id> on a Git remote, only for the run that holds it."""

import argparse
import json
import os
import subprocess
import sys
import uuid


def remote_arg(value):
    """argparse type: a remote name, path or URL, never a git option such as --receive-pack=..."""
    if not value or value.startswith("-"):
        raise argparse.ArgumentTypeError("must be a remote name, path or URL, not an option")
    return value


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def remote_sha(remote, ref):
    result = git("ls-remote", "--refs", remote, ref)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git ls-remote failed")
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1] == ref:
            return fields[0]
    return None


def read_claim(remote, ref):
    # A private temporary ref, not the shared FETCH_HEAD that concurrent runs overwrite.
    temp_ref = f"refs/ai-team-tmp/{uuid.uuid4()}"
    try:
        fetched = git("fetch", "--no-tags", remote, f"+{ref}:{temp_ref}")
        if fetched.returncode:
            raise RuntimeError(fetched.stderr.strip() or "git fetch failed")
        shown = git("show", f"{temp_ref}:claim.json")
        if shown.returncode:
            raise RuntimeError("Claim ref does not contain a readable claim.json")
        return json.loads(shown.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Claim ref contains invalid JSON") from exc
    finally:
        git("update-ref", "-d", temp_ref)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--run-id", default=os.environ.get("RUN_ID"), help="run that holds the claim (default: RUN_ID)")
    parser.add_argument("--remote", default="origin", type=remote_arg)
    args = parser.parse_args()
    ref = f"refs/claims/{args.task_id}"
    check = subprocess.run(["git", "check-ref-format", ref], capture_output=True, text=True)
    if check.returncode or "/" in args.task_id:
        print(f"Invalid task ID for a Git ref: {args.task_id}", file=sys.stderr)
        return 2
    if not args.run_id:
        print("--run-id (or RUN_ID) is required: only the run that holds a claim may release it.", file=sys.stderr)
        return 2
    try:
        sha = remote_sha(args.remote, ref)
        if sha is None:
            print(f"Claim released (or already absent): {args.task_id}.")
            return 0
        holder = read_claim(args.remote, ref).get("run_id")
    except RuntimeError as exc:
        print(f"Retryable Git remote error: {exc}", file=sys.stderr)
        return 3
    if holder != args.run_id:
        print(f"Refusing to release {args.task_id}: it is held by run_id={holder}, not {args.run_id}.", file=sys.stderr)
        return 1
    # The lease makes the delete fail if the claim changed after it was read.
    result = git("push", f"--force-with-lease={ref}:{sha}", args.remote, f":{ref}")
    if result.returncode:
        print(result.stderr.strip() or "Git push failed.", file=sys.stderr)
        return 3
    print(f"Claim released: {args.task_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
