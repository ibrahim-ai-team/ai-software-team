#!/usr/bin/env python3
"""Validate a human approval record for a story checkpoint (read-only)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVALS_DIR = ROOT / ".claude" / "approvals"
CHECKPOINTS = ("CP1", "CP2", "CP3", "CP4")
STORY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", required=True, help="Story identifier, e.g. SHOP-12")
    parser.add_argument(
        "--checkpoint", required=True, choices=CHECKPOINTS, help="Human checkpoint"
    )
    return parser.parse_args(argv)


def is_iso8601(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def validate_record(story: str, checkpoint: str, path: Path) -> tuple[bool, str]:
    if not STORY_PATTERN.fullmatch(story) or story in {".", ".."}:
        return False, "invalid story identifier"
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False, f"approval record not found: {path.name}"
    except UnicodeDecodeError:
        return False, "approval record is not valid UTF-8"
    except OSError:
        return False, "approval record could not be read"

    try:
        record = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, "approval record is not valid JSON"
    if not isinstance(record, dict):
        return False, "approval record must be a JSON object"

    if record.get("checkpoint") != checkpoint:
        return False, "checkpoint does not match requested checkpoint"
    if record.get("story") != story:
        return False, "story does not match requested story"
    if not isinstance(record.get("approved_by"), str) or not record["approved_by"].strip():
        return False, "approved_by must be a non-empty username"
    if not is_iso8601(record.get("date")):
        return False, "date must be an ISO 8601 datetime with timezone"
    if not isinstance(record.get("artifact_hash"), str) or not SHA256_PATTERN.fullmatch(
        record["artifact_hash"]
    ):
        return False, "artifact_hash must be a 64-character SHA-256 hex digest"

    return True, "approval record is valid"


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if not STORY_PATTERN.fullmatch(args.story) or args.story in {".", ".."}:
        print("ERROR: invalid story identifier", file=sys.stderr)
        return 1

    path = APPROVALS_DIR / f"{args.checkpoint}-{args.story}.json"
    valid, message = validate_record(args.story, args.checkpoint, path)
    if valid:
        print(f"PASS: {message}")
        return 0
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
