#!/usr/bin/env python3
"""Validate a passing G1 or G2 record without modifying gate artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES_DIR = ROOT / ".claude" / "gates"
VALID_GATES = ("G1", "G2")
STORY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", required=True, help="Story identifier, e.g. SHOP-12")
    parser.add_argument("--gate", required=True, choices=VALID_GATES, help="Gate to validate")
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


def validate_record(story: str, gate: str, path: Path) -> tuple[bool, str]:
    if not STORY_PATTERN.fullmatch(story) or story in {".", ".."}:
        return False, "invalid story identifier"
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False, f"gate record not found: {path.name}"
    except UnicodeDecodeError:
        return False, "gate record is not valid UTF-8"
    except OSError:
        return False, "gate record could not be read"

    try:
        record = json.loads(raw)
    except json.JSONDecodeError:
        return False, "gate record is not valid JSON"
    if not isinstance(record, dict):
        return False, "gate record must be a JSON object"
    if record.get("passed") is not True:
        return False, "passed must be the boolean true"
    if record.get("reviewer") != "code-review-security":
        return False, "reviewer must be code-review-security"
    if not is_iso8601(record.get("date")):
        return False, "date must be an ISO 8601 datetime with timezone"

    if gate == "G1":
        if not isinstance(record.get("plan_hash"), str) or not SHA256_PATTERN.fullmatch(record["plan_hash"]):
            return False, "plan_hash must be a 64-character SHA-256 hex digest"
    elif gate == "G2":
        checks = record.get("checks")
        if not isinstance(checks, dict):
            return False, "checks must be an object"
        for name in ("lint", "tests", "secrets"):
            if checks.get(name) != "pass":
                return False, f"checks.{name} must equal 'pass'"

    return True, f"{gate} record is valid and passing"


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if not STORY_PATTERN.fullmatch(args.story) or args.story in {".", ".."}:
        print("ERROR: invalid story identifier", file=sys.stderr)
        return 1

    path = GATES_DIR / f"{args.gate}-{args.story}.json"
    valid, message = validate_record(args.story, args.gate, path)
    if valid:
        print(f"PASS: {message}")
        return 0
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
