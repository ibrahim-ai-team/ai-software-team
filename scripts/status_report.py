"""Render and validate the persisted effective status snapshot.

The default view is diagnostic and backward-compatible. Consumers that make
workflow decisions should use --health-json or --strict so an absent, malformed,
or stale snapshot cannot be mistaken for verified empty state.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "state" / "effective.json"
STALE_AFTER_SECONDS = 60 * 60
FUTURE_CLOCK_SKEW_SECONDS = 300
EMPTY_SNAPSHOT: dict[str, Any] = {
    "schema_version": None,
    "generated_at": None,
    "agents": [],
    "tasks": [],
}


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp and normalize it to UTC."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def snapshot_age(snapshot: dict[str, Any], now: datetime) -> int | None:
    """Return snapshot age in whole seconds, or None when generated_at is invalid."""
    generated_at = parse_timestamp(snapshot.get("generated_at"))
    if generated_at is None:
        return None
    return int((now.astimezone(timezone.utc) - generated_at).total_seconds())


def validate_snapshot(snapshot: Any) -> list[str]:
    """Return all structural/identity problems in an effective-state snapshot."""
    problems: list[str] = []
    if not isinstance(snapshot, dict):
        return ["snapshot must be a JSON object"]
    if snapshot.get("schema_version") != 1:
        problems.append("schema_version must be integer 1")
    generated_at = parse_timestamp(snapshot.get("generated_at"))
    if generated_at is None:
        problems.append("generated_at must be an ISO-8601 timestamp with timezone")
    for collection, identifier in (("agents", "agent_id"), ("tasks", "task_id")):
        values = snapshot.get(collection)
        if not isinstance(values, list):
            problems.append(f"{collection} must be a list")
            continue
        seen: set[str] = set()
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                problems.append(f"{collection}[{index}] must be an object")
                continue
            entity_id = item.get(identifier)
            if not isinstance(entity_id, str) or not entity_id.strip():
                problems.append(f"{collection}[{index}].{identifier} must be a non-empty string")
                continue
            normalized = entity_id.casefold()
            if normalized in seen:
                problems.append(f"duplicate {identifier}: {entity_id}")
            seen.add(normalized)
    return problems


def load_snapshot(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Load effective state and return explicit validation errors."""
    if not path.is_file():
        return dict(EMPTY_SNAPSHOT), [f"snapshot not found: {path}"]
    try:
        with path.open(encoding="utf-8") as handle:
            snapshot = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return dict(EMPTY_SNAPSHOT), [f"cannot read snapshot {path}: {exc}"]
    problems = validate_snapshot(snapshot)
    if not isinstance(snapshot, dict):
        return dict(EMPTY_SNAPSHOT), problems
    # Keep invalid collections from causing rendering crashes. The health result
    # still records the schema violation and strict consumers fail closed.
    safe = dict(snapshot)
    for key in ("agents", "tasks"):
        if not isinstance(safe.get(key), list):
            safe[key] = []
    return safe, problems


def filter_snapshot(snapshot: dict[str, Any], expression: str | None) -> dict[str, Any]:
    """Filter one collection while preserving the effective.json top-level schema."""
    filtered = dict(snapshot)
    if expression is None:
        return filtered
    kind, separator, value = expression.partition("=")
    if not separator or kind not in {"agent", "task"} or not value.strip():
        raise ValueError("filter must be agent=X or task=Y")
    value = value.strip().casefold()
    key = "agents" if kind == "agent" else "tasks"
    id_key = "agent_id" if kind == "agent" else "task_id"
    filtered[key] = [
        item for item in snapshot.get(key, []) if isinstance(item, dict) and str(item.get(id_key, "")).casefold() == value
    ]
    other_key = "tasks" if kind == "agent" else "agents"
    filtered[other_key] = []
    return filtered


def display(value: Any) -> str:
    """Use compact, predictable cell values for the human-readable table."""
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "YES" if value else "NO"
    return str(value)


def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Render a fixed-width table sized to the data without exceeding 120 columns."""
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(display(value)))
    widths = [min(width, cap) for width, cap in zip(widths, [24, 16, 16, 5, 10, 15], strict=False)]
    rendered_rows = [[display(value)[: widths[index]] for index, value in enumerate(row)] for row in rows]
    header_line = "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    separator = "  ".join("-" * width for width in widths)
    body = ["  ".join(value.ljust(widths[index]) for index, value in enumerate(row)) for row in rendered_rows]
    return "\n".join([header_line, separator, *body])


def render_human(snapshot: dict[str, Any], expression: str | None, age: int | None, problems: list[str], health: str) -> str:
    """Render health warnings and requested entity rows."""
    lines: list[str] = [f"STATUS HEALTH: {health.upper()}"]
    lines.extend(f"WARNING: {problem}" for problem in problems)
    if age is None:
        if not any("generated_at" in problem for problem in problems):
            lines.append("WARNING: snapshot age unavailable.")
    elif age < -FUTURE_CLOCK_SKEW_SECONDS:
        lines.append(f"WARNING: snapshot timestamp is in the future ({abs(age)}s).")
    elif age >= STALE_AFTER_SECONDS:
        lines.append(f"STALE SNAPSHOT (age: {age}s)")
    kind = expression.partition("=")[0] if expression else None
    if kind in (None, "agent"):
        agents = snapshot.get("agents", [])
        lines.append("Agents")
        lines.append(
            render_table(
                ["agent", "declared", "observed", "drift", "staleness", "last_event_age"],
                [
                    [
                        agent.get("agent_id"),
                        agent.get("declared"),
                        agent.get("observed"),
                        agent.get("drift"),
                        agent.get("staleness"),
                        f"{agent['last_event_age_seconds']}s" if agent.get("last_event_age_seconds") is not None else None,
                    ]
                    for agent in agents
                    if isinstance(agent, dict)
                ],
            )
        )
        if not agents:
            lines.append("(no agents in snapshot)")
    if kind in (None, "task"):
        tasks = snapshot.get("tasks", [])
        if kind == "task" or (expression is None and tasks):
            lines.append("Tasks")
            lines.append(
                render_table(
                    ["task", "declared", "observed", "drift", "staleness", "last_event_age"],
                    [
                        [task.get("task_id"), task.get("declared"), task.get("observed"), task.get("drift"), None, None]
                        for task in tasks
                        if isinstance(task, dict)
                    ],
                )
            )
            if not tasks:
                lines.append("(no tasks in snapshot)")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the snapshot JSON (backward-compatible)")
    parser.add_argument("--health-json", action="store_true", help="emit a health envelope containing snapshot validity and age")
    parser.add_argument(
        "--strict", action="store_true", help="exit non-zero when snapshot is invalid, stale, or has a future timestamp"
    )
    parser.add_argument("--filter", metavar="agent=X|task=Y", help="show only one exact agent_id or task_id (case-insensitive)")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        snapshot, problems = load_snapshot(args.snapshot)
        snapshot = filter_snapshot(snapshot, args.filter)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    age = snapshot_age(snapshot, now)
    if age is not None and age < -FUTURE_CLOCK_SKEW_SECONDS:
        problems.append(f"generated_at is in the future by {abs(age)} seconds")
    stale = age is not None and age >= STALE_AFTER_SECONDS
    if stale:
        problems.append(f"snapshot is stale ({age} seconds old)")
    health = "invalid" if problems else "healthy"
    if args.strict and health != "healthy":
        print(f"ERROR: status snapshot health is {health}: " + "; ".join(problems), file=sys.stderr)
    elif problems:
        for problem in problems:
            print(f"WARNING: {problem}", file=sys.stderr)

    if args.health_json:
        print(
            json.dumps(
                {
                    "status_health": health,
                    "snapshot_valid": not any("stale" not in problem and "future" not in problem for problem in problems),
                    "snapshot_age_seconds": age,
                    "source": str(args.snapshot),
                    "problems": problems,
                    "snapshot": snapshot,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    elif args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        print(render_human(snapshot, args.filter, age, problems, health), end="")
    return 1 if args.strict and health != "healthy" else 0


if __name__ == "__main__":
    raise SystemExit(main())
