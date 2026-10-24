"""Append a validated, secret-safe event to the local JSONL telemetry log."""

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / ".claude" / "telemetry" / "activity.jsonl"
AGENTS_PATH = ROOT / "state" / "agents.json"
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
    parser.add_argument("--agent", help="Legacy agent field; defaults to the resolved agent_id")
    parser.add_argument("--agent-id", default=os.environ.get("AGENT_ID"))
    parser.add_argument("--session-id", default=os.environ.get("SESSION_ID"))
    parser.add_argument("--run-id", default=os.environ.get("RUN_ID"))
    parser.add_argument("--action", required=True, choices=sorted(ALLOWED_ACTIONS))
    parser.add_argument("--story", required=True)
    parser.add_argument("--details", required=True, help="JSON object with non-sensitive event details")
    return parser.parse_args()


def validate_agent_id(agent_id: str, path: Path | None = None) -> str:
    """Return a canonical agent ID or raise ValueError with a clear explanation."""
    path = path or AGENTS_PATH
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError("agent_id is required (use --agent-id, --agent, or AGENT_ID).")
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read canonical agent registry at {path}.") from exc
    canonical_ids = registry.get("agent_ids") if isinstance(registry, dict) else None
    if not isinstance(canonical_ids, list) or not all(isinstance(item, str) for item in canonical_ids):
        raise ValueError(f"canonical agent registry at {path} must contain an agent_ids array.")
    if agent_id not in canonical_ids:
        raise ValueError(f"unknown agent_id '{agent_id}'; add it to {path} only if it is a canonical agent.")
    return agent_id


def resolve_uuid4(value: str | None, field: str) -> str:
    """Use a supplied UUID4 or generate one when the caller omits the identifier."""
    if value is None:
        return str(uuid.uuid4())
    if not value.strip():
        raise ValueError(f"{field} must be a UUID4.")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field} must be a UUID4.") from exc
    if parsed.version != 4:
        raise ValueError(f"{field} must be a UUID4.")
    return str(parsed)


def canonical_json(obj: Any) -> str:
    """Serialize JSON deterministically for the telemetry hash chain."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def previous_event_hash(path: Path | None = None) -> str:
    """Return the last recorded hash, or genesis for a new/empty log."""
    path = path or LOG_PATH
    if not path.exists() or path.stat().st_size == 0:
        return "genesis"
    try:
        with path.open(encoding="utf-8") as handle:
            lines = [line for line in handle if line.strip()]
        last_event = json.loads(lines[-1])
        value = last_event.get("event_hash") if isinstance(last_event, dict) else None
    except (OSError, json.JSONDecodeError, IndexError) as exc:
        raise ValueError("cannot append to telemetry: last event is unreadable or malformed") from exc
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("cannot append to telemetry: last event has no valid event_hash")
    return value


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
        if value is not None and not value.strip():
            print(f"ERROR: {name} must not be empty.", file=sys.stderr)
            return 1
    if not args.story.strip():
        print("ERROR: --story must not be empty.", file=sys.stderr)
        return 1
    forbidden = contains_forbidden_key(details)
    if forbidden:
        print("ERROR: sensitive field name rejected; telemetry event was not written.", file=sys.stderr)
        return 1

    agent_id = args.agent_id or args.agent
    try:
        agent_id = validate_agent_id(agent_id)
        session_id = resolve_uuid4(args.session_id, "session_id")
        run_id = resolve_uuid4(args.run_id, "run_id")
        event_id = str(uuid.uuid4())
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent or agent_id,
        "action": args.action,
        "story": args.story,
        "details": details,
        "trace_id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "session_id": session_id,
        "run_id": run_id,
        "event_id": event_id,
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        event["prev_hash"] = previous_event_hash()
        event_payload = {key: value for key, value in event.items() if key not in {"prev_hash", "event_hash"}}
        event["event_hash"] = hashlib.sha256((event["prev_hash"] + canonical_json(event_payload)).encode("utf-8")).hexdigest()
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    except (OSError, ValueError) as exc:
        print(f"ERROR: unable to append telemetry ({exc}).", file=sys.stderr)
        return 1
    print(f"Telemetry appended: {event['event_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
