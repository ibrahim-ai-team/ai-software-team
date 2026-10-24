"""Summarize the local append-only JSONL telemetry log."""

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / ".claude" / "telemetry" / "activity.jsonl"
IDENTITY_FIELDS = ("agent_id", "session_id", "run_id", "event_id")


def parse_timestamp(value: Any) -> datetime:
    """Parse an ISO 8601 timestamp, including a trailing Z."""
    if not isinstance(value, str):
        raise ValueError("timestamp is not a string")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_events(path: Path = LOG_PATH) -> list[dict[str, Any]]:
    """Load valid event objects; report malformed lines and continue."""
    if not path.exists():
        return []
    events = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if isinstance(event, dict) and isinstance(event.get("ts"), str):
                    parse_timestamp(event["ts"])
                    events.append(event)
                else:
                    print(f"WARNING: skipped invalid event on line {line_number}")
            except (json.JSONDecodeError, ValueError):
                print(f"WARNING: skipped invalid event on line {line_number}")
    return events


def summarize(events: list[dict[str, Any]]) -> str:
    """Return a stable summary, including a count of legacy events."""
    by_agent = Counter(str(event.get("agent", "unknown")) for event in events)
    errors = sum(event.get("action") == "error" for event in events)
    gates = sum(event.get("action") == "gate" for event in events)
    legacy_events = sum(any(not event.get(field) for field in IDENTITY_FIELDS) for event in events)
    story_times: dict[str, list[datetime]] = defaultdict(list)
    for event in events:
        story = str(event.get("story", "none"))
        if story and story != "none":
            try:
                story_times[story].append(parse_timestamp(event["ts"]))
            except (KeyError, ValueError):
                continue
    durations = []
    for timestamps in story_times.values():
        normalized = []
        for stamp in timestamps:
            if stamp.tzinfo is None:
                stamp = stamp.astimezone()
            normalized.append(stamp.timestamp())
        durations.append(max(normalized) - min(normalized) if len(normalized) > 1 else 0.0)
    average = sum(durations) / len(durations) if durations else 0.0
    agents = ", ".join(f"{agent}={count}" for agent, count in sorted(by_agent.items())) or "none"
    return (
        f"Events: {len(events)} | Actions by agent: {agents}\\n"
        f"Errors: {errors} | Gates recorded: {gates} | Legacy events: {legacy_events}\\n"
        f"Stories: {len(story_times)} | Average duration: {average:.2f}s"
    )


def main() -> int:
    print(summarize(load_events()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
