"""Verify the tamper-evident hash chain in the local telemetry JSONL log."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / ".claude" / "telemetry" / "activity.jsonl"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_json(obj: Any) -> str:
    """Serialize JSON deterministically for the telemetry hash chain."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def verify_file(path: Path) -> int:
    """Return 0 for a valid or empty log, otherwise report the first failure."""
    if not path.exists() or path.stat().st_size == 0:
        print("Telemetry verification: nothing to verify.")
        return 0

    expected_prev_hash = "genesis"
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: unable to read telemetry: {exc.__class__.__name__}", file=sys.stderr)
        return 1

    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                print(f"ERROR: line {line_number}: invalid JSON.", file=sys.stderr)
                return 1
            if not isinstance(event, dict):
                print(f"ERROR: line {line_number}: event must be a JSON object.", file=sys.stderr)
                return 1

            if "prev_hash" not in event or "event_hash" not in event:
                print(
                    f"ERROR: line {line_number}: legacy events detected (missing prev_hash/event_hash).",
                    file=sys.stderr,
                )
                return 1

            prev_hash = event["prev_hash"]
            event_hash = event["event_hash"]
            if prev_hash != expected_prev_hash:
                print(
                    f"ERROR: line {line_number}: prev_hash mismatch; expected {expected_prev_hash!r}.",
                    file=sys.stderr,
                )
                return 1
            if not isinstance(event_hash, str) or not HASH_RE.fullmatch(event_hash):
                print(f"ERROR: line {line_number}: event_hash must be 64 lowercase hex characters.", file=sys.stderr)
                return 1

            payload = {key: value for key, value in event.items() if key not in {"prev_hash", "event_hash"}}
            calculated = hashlib.sha256((prev_hash + canonical_json(payload)).encode("utf-8")).hexdigest()
            if calculated != event_hash:
                print(f"ERROR: line {line_number}: event_hash mismatch; event content may be modified.", file=sys.stderr)
                return 1
            expected_prev_hash = event_hash

    print("Telemetry verification: hash chain intact.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=LOG_PATH, help="JSONL telemetry file to verify")
    args = parser.parse_args()
    return verify_file(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
