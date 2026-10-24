#!/usr/bin/env python3
"""Render the persisted effective status snapshot for people or programs.

This command deliberately reads only state/effective.json. It never attempts
to reconstruct effective state from project-state.md or telemetry.
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
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def snapshot_age(snapshot: dict[str, Any], now: datetime) -> int | None:
    """Return snapshot age in whole seconds, or None when generated_at is invalid."""
    generated_at = parse_timestamp(snapshot.get("generated_at"))
    if generated_at is None:
        return None
    return max(0, int((now.astimezone(timezone.utc) - generated_at).total_seconds()))


def load_snapshot(path: Path) -> dict[str, Any]:
    """Load effective state; degrade gracefully if it is absent or invalid."""
    if not path.is_file():
        print(f"WARNING: effective status snapshot not found: {path}", file=sys.stderr)
        return dict(EMPTY_SNAPSHOT)
    try:
        with path.open(encoding="utf-8") as handle:
            snapshot = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARNING: cannot read effective status snapshot {path}: {exc}", file=sys.stderr)
        return dict(EMPTY_SNAPSHOT)
    if not isinstance(snapshot, dict):
        print(f"WARNING: effective status snapshot is not a JSON object: {path}", file=sys.stderr)
        return dict(EMPTY_SNAPSHOT)
    for key in ("agents", "tasks"):
        if not isinstance(snapshot.get(key, []), list):
            print(f"WARNING: invalid '{key}' collection in effective status snapshot.", file=sys.stderr)
            snapshot[key] = []
    return snapshot


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
        item
        for item in snapshot.get(key, [])
        if isinstance(item, dict) and str(item.get(id_key, "")).casefold() == value
    ]
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
    # Cap long identifiers/evidence values to keep the standard view compact.
    widths = [min(width, cap) for width, cap in zip(widths, [24, 16, 16, 5, 10, 15], strict=False)]
    rendered_rows = [[display(value)[:widths[index]] for index, value in enumerate(row)] for row in rows]
    header_line = "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    separator = "  ".join("-" * width for width in widths)
    body = [
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rendered_rows
    ]
    return "\n".join([header_line, separator, *body])


def render_human(snapshot: dict[str, Any], expression: str | None, age: int | None) -> str:
    """Render agent rows and, when requested, task rows."""
    lines: list[str] = []
    if age is None:
        lines.append("WARNING: snapshot age unavailable (generated_at missing or invalid).")
    elif age > STALE_AFTER_SECONDS:
        lines.append(f"STALE SNAPSHOT (age: {age}s)")
    elif age == STALE_AFTER_SECONDS:
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
                        (
                            f"{agent['last_event_age_seconds']}s"
                            if agent.get("last_event_age_seconds") is not None
                            else None
                        ),
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
                        [
                            task.get("task_id"),
                            task.get("declared"),
                            task.get("observed"),
                            task.get("drift"),
                            None,
                            None,
                        ]
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
    parser.add_argument("--json", action="store_true", help="emit JSON to stdout for pipes")
    parser.add_argument(
        "--filter",
        metavar="agent=X|task=Y",
        help="show only one exact agent_id or task_id (case-insensitive)",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=DEFAULT_SNAPSHOT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        snapshot = load_snapshot(args.snapshot)
        snapshot = filter_snapshot(snapshot, args.filter)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    age = snapshot_age(snapshot, datetime.now(timezone.utc))
    if age is None:
        print("WARNING: snapshot age unavailable (generated_at missing or invalid).", file=sys.stderr)
    elif age > STALE_AFTER_SECONDS:
        print(f"WARNING: STALE SNAPSHOT (age: {age}s)", file=sys.stderr)

    if args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        print(render_human(snapshot, args.filter, age), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
