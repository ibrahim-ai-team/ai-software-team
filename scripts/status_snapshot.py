#!/usr/bin/env python3
"""Reconcile declared project state with observed telemetry and optional GitHub state.

Claims in project-state.md are context, not proof. Only explicit, parseable
observations produce an observed status or a drift finding.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "project-state.md"
DEFAULT_LOG = ROOT / ".claude" / "telemetry" / "activity.jsonl"
DEFAULT_OUTPUT = ROOT / "state" / "effective.json"
FRESH_SECONDS = 900
STALE_SECONDS = 86400
TASK_STATUSES = {
    "draft": "DRAFT", "ready": "READY", "in progress": "IN_PROGRESS",
    "blocked": "BLOCKED", "in review": "IN_REVIEW", "done": "DONE",
    "cancelled": "CANCELLED",
}
AGENT_STATUSES = {"running", "idle", "blocked", "completed", "cancelled", "unknown"}


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        stamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def normalize_status(value: str, *, agent: bool = False) -> str:
    text = value.strip().casefold().replace("-", "_").replace(" ", "_")
    if agent:
        aliases = {"in_progress": "running", "active": "running", "done": "completed",
                   "complete": "completed", "finished": "completed", "waiting": "idle"}
        text = aliases.get(text, text)
        return text if text in AGENT_STATUSES else "unknown"
    aliases = {"in_progress": "IN_PROGRESS", "in_review": "IN_REVIEW"}
    return aliases.get(text, TASK_STATUSES.get(value.strip().casefold(), text.upper()))


def parse_state(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Parse only the documented Backlog and Active delegations Markdown tables."""
    agents: dict[str, dict[str, Any]] = {}
    tasks: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        print(f"WARNING: project state file not found: {path}", file=sys.stderr)
        return agents, tasks

    section = ""
    headers: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            section = line.lstrip("#").strip().casefold()
            headers = []
            continue
        if section not in {"backlog and task ownership", "active delegations"}:
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if not headers:
            headers = [cell.casefold() for cell in cells]
            continue
        if not cells or all(set(cell) <= set("-: ") for cell in cells):
            continue
        row = dict(zip(headers, cells))
        if section == "backlog and task ownership":
            task_id = row.get("task id", "")
            status = row.get("status", "")
            if task_id and task_id.casefold() != "task id" and status:
                tasks[task_id] = {
                    "status": normalize_status(status),
                    "priority": row.get("priority", "") or None,
                    "owner": row.get("owner", "") or None,
                    "source": "project-state.md",
                }
        else:
            task_id = row.get("task id", "")
            owner = row.get("owner", "")
            status = row.get("status", "")
            delegation_id = row.get("delegation id", "")
            if task_id and task_id.casefold() != "task id":
                task = tasks.setdefault(task_id, {"status": None, "source": "project-state.md"})
                task["delegations"] = task.get("delegations", [])
                task["delegations"].append({
                    "delegation_id": delegation_id or None,
                    "owner": owner or None,
                    "status": normalize_status(status, agent=True) if status else None,
                })
                if owner:
                    agent_id = owner.casefold().replace(" ", "-")
                    item = agents.setdefault(agent_id, {"status": None, "source": "project-state.md"})
                    item["declared"] = normalize_status(status, agent=True) if status else None
                    item["task_id"] = task_id
    return agents, tasks


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.is_file():
        return events
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                print(f"WARNING: skipped malformed telemetry JSON on line {line_no}", file=sys.stderr)
                continue
            if not isinstance(event, dict) or not parse_time(event.get("ts")):
                print(f"WARNING: skipped telemetry event with invalid timestamp on line {line_no}", file=sys.stderr)
                continue
            events.append(event)
    return events


def latest_by(events: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in events:
        value = event.get(key)
        if not isinstance(value, str) or not value.strip() or value.casefold() == "none":
            continue
        stamp = parse_time(event.get("ts"))
        if stamp and (value not in latest or stamp > parse_time(latest[value]["ts"])):
            latest[value] = event
    return latest


def event_agent_status(event: dict[str, Any]) -> str | None:
    details = event.get("details")
    if isinstance(details, dict):
        for key in ("status", "agent_status", "outcome"):
            value = details.get(key)
            if isinstance(value, str):
                normalized = normalize_status(value, agent=True)
                if normalized != "unknown":
                    return normalized
        target = details.get("target")
        if isinstance(target, str) and target.strip():
            return "running"
    action = event.get("action")
    # Event actions alone do not prove an agent failed, completed, or is idle.
    if action == "delegate":
        return "running"
    return None


def run_gh(args: list[str]) -> list[dict[str, Any]] | None:
    if not shutil.which("gh"):
        return None
    try:
        proc = subprocess.run(["gh", *args], cwd=ROOT, text=True, capture_output=True, check=False, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"WARNING: GitHub CLI command unavailable ({type(exc).__name__}); omitting GitHub observations.", file=sys.stderr)
        return None
    if proc.returncode != 0:
        print("WARNING: GitHub CLI query failed; omitting GitHub observations.", file=sys.stderr)
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("WARNING: GitHub CLI returned invalid JSON; omitting GitHub observations.", file=sys.stderr)
        return None
    return data if isinstance(data, list) else None


def get_github() -> dict[str, Any] | None:
    issues = run_gh(["issue", "list", "--state", "all", "--limit", "500",
                     "--json", "number,title,body,state,labels,updatedAt"])
    if issues is None:
        return None
    prs = run_gh(["pr", "list", "--state", "all", "--limit", "500",
                  "--json", "number,title,body,state,isDraft,updatedAt"])
    if prs is None:
        return None
    return {"issues": issues, "pull_requests": prs}


def issue_status(issue: dict[str, Any]) -> str:
    return "DONE" if str(issue.get("state", "")).casefold() == "closed" else "IN_PROGRESS"


def build_snapshot(state_path: Path, log_path: Path, now: datetime) -> dict[str, Any]:
    declared_agents, declared_tasks = parse_state(state_path)
    events = load_events(log_path)
    latest_agents = latest_by(events, "agent_id")
    latest_tasks = latest_by(events, "story")
    agent_ids = sorted(set(declared_agents) | set(latest_agents))
    agents = []
    for agent_id in agent_ids:
        declared_record = declared_agents.get(agent_id, {})
        event = latest_agents.get(agent_id)
        stamp = parse_time(event.get("ts")) if event else None
        age = max(0, int((now - stamp).total_seconds())) if stamp else None
        staleness = ("UNKNOWN" if age is None or age > STALE_SECONDS else
                     "FRESH" if age < FRESH_SECONDS else "STALE")
        observed_status = event_agent_status(event) if event else None
        declared_status = declared_record.get("declared")
        reliable = observed_status is not None
        agents.append({
            "agent_id": agent_id,
            "declared": declared_status,
            "observed": observed_status,
            "drift": bool(reliable and declared_status is not None and declared_status != observed_status),
            "last_event_age_seconds": age,
            "staleness": staleness,
        })

    github = get_github()
    tasks = []
    task_ids = sorted(set(declared_tasks) | set(latest_tasks))
    for task_id in task_ids:
        declared_record = declared_tasks.get(task_id, {})
        event = latest_tasks.get(task_id)
        observed = None
        evidence: list[dict[str, Any]] = []
        if event:
            details = event.get("details")
            candidate = details.get("task_status") if isinstance(details, dict) else None
            if isinstance(candidate, str):
                observed = normalize_status(candidate)
                evidence.append({"source": "telemetry", "event_id": event.get("event_id"), "ts": event.get("ts")})
        if github is not None:
            for issue in github["issues"]:
                searchable = f"{issue.get('title', '')} {issue.get('body', '')}"
                if task_id.casefold() in searchable.casefold():
                    issue_observed = issue_status(issue)
                    observed = issue_observed
                    evidence.append({"source": "github_issue", "number": issue.get("number"),
                                     "state": issue.get("state"), "url": issue.get("url")})
            for pr in github["pull_requests"]:
                searchable = f"{pr.get('title', '')} {pr.get('body', '')}"
                if task_id.casefold() in searchable.casefold():
                    evidence.append({"source": "github_pull_request", "number": pr.get("number"),
                                     "state": pr.get("state"), "is_draft": pr.get("isDraft")})
                    if observed is None and str(pr.get("state", "")).casefold() == "open":
                        observed = "IN_REVIEW"
        declared_status = declared_record.get("status")
        tasks.append({
            "task_id": task_id,
            "declared": declared_status,
            "observed": observed,
            "drift": bool(observed is not None and declared_status is not None and declared_status != observed),
            "evidence": evidence,
        })

    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agents": agents,
        "tasks": tasks,
    }
    if github is not None:
        snapshot["github"] = {
            "available": True,
            "issues_count": len(github["issues"]),
            "pull_requests_count": len(github["pull_requests"]),
        }
    else:
        print("WARNING: GitHub observations omitted (gh missing or query unavailable).", file=sys.stderr)
    return snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE, help="project-state.md path")
    parser.add_argument("--activity", type=Path, default=DEFAULT_LOG, help="activity.jsonl path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="snapshot output path")
    parser.add_argument("--fresh-seconds", type=int, default=FRESH_SECONDS)
    parser.add_argument("--stale-seconds", type=int, default=STALE_SECONDS)
    parser.add_argument("--dry-run", action="store_true", help="print JSON without writing a file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fresh_seconds < 0 or args.stale_seconds < args.fresh_seconds:
        print("ERROR: thresholds must satisfy 0 <= fresh-seconds <= stale-seconds.", file=sys.stderr)
        return 2
    global FRESH_SECONDS, STALE_SECONDS
    FRESH_SECONDS, STALE_SECONDS = args.fresh_seconds, args.stale_seconds
    snapshot = build_snapshot(args.state, args.activity, datetime.now(timezone.utc))
    rendered = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    if args.dry_run:
        print(rendered, end="")
        return 0
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot write snapshot to {args.output}: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote effective status snapshot: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
