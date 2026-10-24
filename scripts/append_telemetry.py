#!/usr/bin/env python3
"""Append a validated, secret-safe event to the local JSONL telemetry log."""

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / ".claude" / "telemetry" / "activity.jsonl"
ALLOWED_ACTIONS = {"delegate", "gate", "approve", "tool_call", "error"}
FORBIDDEN_KEY_PARTS = ("token", "password", "api_key", "secret")


def contains_forbidden_key(value: Any) -> str | None:
    """Return a sensitive key path, recursively, without exposing its value."""
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if any(part in key_text.casefold() for part in FORBIDDEN_KEY_PARTS):
                return key_text
            nested = contains_forbidden_key(child)
            if nested:
                return nested
    elif isinstance(value, list):
        for child in value:
            nested = contains_forbidden_key(child)
            if nested:
                return nested
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--action", required=True, choices=sorted(ALLOWED_ACTIONS))
    parser.add_argument("--story", required=True)
    parser.add_argument("--details", required=True, help="JSON object with non-sensitive event details")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        details = json.loads(args.details)
    except json.JSONDecodeError:
        print("ERROR: --details must be valid JSON.", file=sys.stderr)
        return 1

    if not isinstance(details, dict):
        print("ERROR: --details must be a JSON object.", file=sys.stderr)
        return 1
    for name, value in (("--agent", args.agent), ("--story", args.story)):
        if not value.strip():
            print(f"ERROR: {name} must not be empty.", file=sys.stderr)
            return 1
    forbidden = contains_forbidden_key(details)
    if forbidden:
        print("ERROR: sensitive field name rejected; telemetry event was not written.", file=sys.stderr)
        return 1

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent,
        "action": args.action,
        "story": args.story,
        "details": details,
        "trace_id": str(uuid.uuid4()),
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    except OSError as exc:
        print(f"ERROR: unable to append telemetry ({exc.__class__.__name__}).", file=sys.stderr)
        return 1
    print(f"Telemetry appended: {event['trace_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
