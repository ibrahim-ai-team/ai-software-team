#!/usr/bin/env python3
"""List active refs/claims/* on a Git remote and print their claim metadata."""

import argparse
import json
import subprocess
import sys
import uuid


def git(*args, check=True):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


def remote_arg(value):
    """argparse type: a remote name, path or URL, never a git option such as --upload-pack=..."""
    if not value or value.startswith("-"):
        raise argparse.ArgumentTypeError("must be a remote name, path or URL, not an option")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", default="origin", type=remote_arg)
    args = parser.parse_args()
    result = git("ls-remote", "--refs", args.remote, "refs/claims/*", check=False)
    if result.returncode:
        print(result.stderr.strip() or "git ls-remote failed.", file=sys.stderr)
        return 3
    entries = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1].startswith("refs/claims/"):
            entries.append((fields[1], fields[0]))
    if not entries:
        print("No active claims.")
        return 0
    for ref, _sha in sorted(entries):
        # A private temporary ref, not the shared FETCH_HEAD that concurrent runs overwrite.
        temp_ref = f"refs/ai-team-tmp/{uuid.uuid4()}"
        fetched = git("fetch", "--no-tags", args.remote, f"+{ref}:{temp_ref}", check=False)
        if fetched.returncode:
            print(f"Could not read {ref}: {fetched.stderr.strip()}", file=sys.stderr)
            return 3
        shown = git("show", f"{temp_ref}:claim.json", check=False)
        git("update-ref", "-d", temp_ref, check=False)
        if shown.returncode:
            print(f"Could not parse {ref}: claim.json is missing.", file=sys.stderr)
            return 1
        try:
            claim = json.loads(shown.stdout)
        except json.JSONDecodeError:
            print(f"Could not parse {ref}: invalid claim.json.", file=sys.stderr)
            return 1
        print(
            f"{claim.get('task_id', ref.removeprefix('refs/claims/'))}: "
            f"run_id={claim.get('run_id', 'unknown')} "
            f"agent_id={claim.get('agent_id', 'unknown')} "
            f"session_id={claim.get('session_id', 'unknown')} "
            f"claimed_at={claim.get('claimed_at', 'unknown')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
