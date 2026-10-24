"""Manage a local single-coordinator lock with a time-to-live.

This is a same-machine coordination aid, not a distributed lock service.
"""

from __future__ import annotations

import argparse
from contextlib import suppress
import getpass
import json
import os
import socket
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK_PATH = ROOT / "state" / "coordinator.lock"
DEFAULT_TTL_SECONDS = 3600
LOCK_FIELDS = {"pid", "hostname", "started_at", "ttl_seconds", "holder"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def read_lock(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"lock file contains invalid JSON: {path}") from exc
    if not isinstance(data, dict) or not LOCK_FIELDS.issubset(data):
        raise ValueError(f"lock file must contain fields: {', '.join(sorted(LOCK_FIELDS))}")
    if not isinstance(data["pid"], int) or isinstance(data["pid"], bool):
        raise ValueError("lock field 'pid' must be an integer")
    if not isinstance(data["hostname"], str) or not data["hostname"]:
        raise ValueError("lock field 'hostname' must be a non-empty string")
    if not isinstance(data["holder"], str) or not data["holder"]:
        raise ValueError("lock field 'holder' must be a non-empty string")
    if not isinstance(data["ttl_seconds"], int) or isinstance(data["ttl_seconds"], bool) or data["ttl_seconds"] <= 0:
        raise ValueError("lock field 'ttl_seconds' must be a positive integer")
    if parse_timestamp(data["started_at"]) is None:
        raise ValueError("lock field 'started_at' must be an ISO 8601 timestamp")
    return data


def is_expired(lock: dict[str, Any], now: datetime) -> bool:
    started_at = parse_timestamp(lock["started_at"])
    assert started_at is not None
    return now >= started_at + timedelta(seconds=lock["ttl_seconds"])


def create_lock(path: Path, ttl_seconds: int) -> dict[str, Any]:
    lock = {
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "started_at": utc_now().isoformat().replace("+00:00", "Z"),
        "ttl_seconds": ttl_seconds,
        "holder": getpass.getuser() or "unknown",
    }
    rendered = json.dumps(lock, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    return lock


def acquire(path: Path, ttl_seconds: int) -> int:
    if ttl_seconds <= 0:
        print("ERROR: --ttl must be a positive number of seconds.", file=sys.stderr)
        return 2
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        create_lock(path, ttl_seconds)
        print(f"Lock acquired: {path}")
        return 0
    except FileExistsError:
        pass
    try:
        existing = read_lock(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if existing is None:
        # The prior holder may have released between O_EXCL and read_lock.
        try:
            create_lock(path, ttl_seconds)
            print(f"Lock acquired: {path}")
            return 0
        except FileExistsError:
            existing = read_lock(path)
            if existing is None:
                print("ERROR: lock changed while acquiring; retry the command.", file=sys.stderr)
                return 2
    now = utc_now()
    if not is_expired(existing, now):
        print(
            f"Lock held by PID {existing['pid']} on {existing['hostname']} "
            f"(holder: {existing['holder']}, started_at: {existing['started_at']}, "
            f"TTL: {existing['ttl_seconds']}s).",
            file=sys.stderr,
        )
        return 2

    stale_path = path.with_name(f"{path.name}.expired-{uuid.uuid4().hex}")
    try:
        # Rename is atomic on the same filesystem. Only one contender can move
        # the existing lock; the replacement itself is created exclusively.
        os.rename(path, stale_path)
    except FileNotFoundError:
        # Another process released or replaced the stale lock; retry once.
        try:
            create_lock(path, ttl_seconds)
            print(f"Lock acquired: {path}")
            return 0
        except FileExistsError:
            try:
                current = read_lock(path)
            except ValueError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 2
            if current is not None:
                print(
                    f"Lock held by PID {current['pid']} on {current['hostname']} (holder: {current['holder']}).",
                    file=sys.stderr,
                )
            return 2
    try:
        # Re-check the moved file: do not steal a replacement that appeared
        # after the original read.
        moved = read_lock(stale_path)
        if moved is None or not is_expired(moved, utc_now()):
            if moved is not None:
                try:
                    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                        handle.write(json.dumps(moved, indent=2) + "\n")
                except FileExistsError:
                    pass
            print("ERROR: lock changed while acquiring; retry the command.", file=sys.stderr)
            return 2
        print(
            f"WARNING: expired lock for PID {moved['pid']} on {moved['hostname']} "
            f"(started_at: {moved['started_at']}); taking over.",
            file=sys.stderr,
        )
        try:
            create_lock(path, ttl_seconds)
        except FileExistsError:
            current = read_lock(path)
            if current is not None:
                print(
                    f"Lock held by PID {current['pid']} on {current['hostname']} "
                    f"(holder: {current['holder']}).",
                    file=sys.stderr,
                )
            return 2
        print(f"Lock acquired: {path}")
        return 0
    finally:
        with suppress(FileNotFoundError):
            stale_path.unlink()


def release(path: Path) -> int:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(f"ERROR: could not release lock {path}: {exc}", file=sys.stderr)
        return 1
    print("Lock released.")
    return 0


def show_status(path: Path) -> int:
    try:
        lock = read_lock(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if lock is None:
        print("no lock")
    else:
        print(json.dumps(lock, indent=2, ensure_ascii=False))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock-path", type=Path, default=DEFAULT_LOCK_PATH, help="lock file path")
    subparsers = parser.add_subparsers(dest="command", required=True)
    acquire_parser = subparsers.add_parser("acquire", help="acquire the coordinator lock")
    acquire_parser.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS, help="lock TTL in seconds (default: 3600)")
    subparsers.add_parser("release", help="release the coordinator lock")
    subparsers.add_parser("status", help="show the coordinator lock")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "acquire":
        return acquire(args.lock_path, args.ttl)
    if args.command == "release":
        return release(args.lock_path)
    return show_status(args.lock_path)


if __name__ == "__main__":
    raise SystemExit(main())
