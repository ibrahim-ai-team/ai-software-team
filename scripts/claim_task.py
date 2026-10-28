#!/usr/bin/env python3
"""Atomically claim a task by creating refs/claims/<task-id> on a Git remote."""

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone


def git(*args, input_text=None, check=True):
    return subprocess.run(
        ["git", *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=check,
    )


def remote_arg(value):
    """argparse type: a remote name, path or URL, never a git option such as --upload-pack=..."""
    if not value or value.startswith("-"):
        raise argparse.ArgumentTypeError("must be a remote name, path or URL, not an option")
    return value


def task_ref(task_id):
    ref = f"refs/claims/{task_id}"
    try:
        git("check-ref-format", ref)
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"Invalid task ID for a Git ref: {task_id}") from exc
    if "/" in task_id or task_id in {".", ".."}:
        raise ValueError("Task ID must be one path component (no slash).")
    return ref


def remote_sha(remote, ref):
    result = git("ls-remote", "--refs", remote, ref, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git ls-remote failed")
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1] == ref:
            return fields[0]
    return None


def read_claim(remote, ref):
    # Fetch the advertised claim ref into a private temporary ref (not the shared FETCH_HEAD,
    # which concurrent runs overwrite) so its JSON can be inspected without GitHub APIs.
    temp_ref = f"refs/ai-team-tmp/{uuid.uuid4()}"
    try:
        result = git("fetch", "--no-tags", remote, f"+{ref}:{temp_ref}", check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "git fetch failed")
        result = git("show", f"{temp_ref}:claim.json", check=False)
        if result.returncode:
            raise RuntimeError("Claim ref does not contain a readable claim.json")
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Claim ref contains invalid JSON") from exc
    finally:
        git("update-ref", "-d", temp_ref, check=False)


def create_orphan_commit(payload):
    blob = git("hash-object", "-w", "--stdin", input_text=json.dumps(payload, sort_keys=True, indent=2) + "\n").stdout.strip()
    tree = git("mktree", input_text=f"100644 blob {blob}\tclaim.json\n").stdout.strip()
    return git("commit-tree", tree, "-m", f"Claim task {payload['task_id']}").stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--remote", default="origin", type=remote_arg)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        ref = task_ref(args.task_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    run_id = args.run_id or os.environ.get("RUN_ID") or str(uuid.uuid4())
    payload = {
        "task_id": args.task_id,
        "run_id": run_id,
        "session_id": os.environ.get("SESSION_ID") or str(uuid.uuid4()),
        "agent_id": os.environ.get("AGENT_ID") or "unknown",
        "claimed_at": datetime.now(timezone.utc).isoformat(),
    }

    if args.dry_run:
        print(json.dumps(payload, sort_keys=True, indent=2))
        print(f"DRY RUN: git push {args.remote} <orphan-commit-sha>:{ref} --force-with-lease={ref}:")
        return 0

    try:
        existing = remote_sha(args.remote, ref)
        if existing:
            current = read_claim(args.remote, ref)
            if current.get("run_id") == run_id:
                print(f"Claim already held by this run ({run_id}) for {args.task_id}.")
                return 0
            print(
                f"Claim unavailable: task {args.task_id} is held by "
                f"run_id={current.get('run_id', 'unknown')}, "
                f"agent_id={current.get('agent_id', 'unknown')}, "
                f"session_id={current.get('session_id', 'unknown')}.",
                file=sys.stderr,
            )
            return 1

        commit = create_orphan_commit(payload)
        push = git(
            "push",
            args.remote,
            f"{commit}:{ref}",
            f"--force-with-lease={ref}:",
            check=False,
        )
        if push.returncode == 0:
            print(f"Claim acquired: {args.task_id} (run_id={run_id}).")
            return 0

        # Another contender may have won between ls-remote and push.
        winner = remote_sha(args.remote, ref)
        if winner:
            current = read_claim(args.remote, ref)
            if current.get("run_id") == run_id:
                print(f"Claim already held by this run ({run_id}) for {args.task_id}.")
                return 0
            print(
                f"Claim unavailable: task {args.task_id} is held by "
                f"run_id={current.get('run_id', 'unknown')}, "
                f"agent_id={current.get('agent_id', 'unknown')}, "
                f"session_id={current.get('session_id', 'unknown')}.",
                file=sys.stderr,
            )
            return 1
        print(push.stderr.strip() or "Git push failed and no claim ref is visible.", file=sys.stderr)
        return 3
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Retryable Git remote error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
