"""Read-only, fail-closed detector for unresolved story disagreements."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISAGREEMENTS_DIR = ROOT / ".claude" / "disagreements"
APPROVERS_PATH = ROOT / ".claude" / "human-approvers.json"
# Accepted decided_by values until the sponsor lists approvers by username.
GENERIC_DECIDERS = {"human sponsor", "sponsor", "human"}
STORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
AGENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", required=True, help="Story identifier, e.g. US-123")
    parser.add_argument(
        "--agents",
        required=True,
        help="Comma-separated involved agent identifiers, e.g. software-architect,tech-lead",
    )
    return parser


def _configured_approvers() -> set[str] | None:
    """GitHub usernames from .claude/human-approvers.json, or None when the sponsor has not created it."""
    try:
        data = json.loads(APPROVERS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError):
        return set()  # unreadable or malformed: fail closed, nobody is an approver
    names = data.get("approvers") if isinstance(data, dict) else None
    if not isinstance(names, list):
        return set()
    return {name.strip().casefold() for name in names if isinstance(name, str) and name.strip()}


def _has_human_decision(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    decision = record.get("human_decision")
    if not isinstance(decision, dict):
        return False
    decided_by = decision.get("decided_by")
    decision_text = decision.get("decision")
    if not isinstance(decided_by, str) or not decided_by.strip():
        return False
    # Exact match only: a substring test accepted values such as "not human".
    approvers = _configured_approvers()
    if decided_by.strip().casefold() not in (GENERIC_DECIDERS if approvers is None else approvers):
        return False
    return isinstance(decision_text, str) and bool(decision_text.strip())


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not STORY_RE.fullmatch(args.story):
        print("Invalid story identifier.", file=sys.stderr)
        return 2
    agents = [item.strip() for item in args.agents.split(",")]
    if not agents or any(not item or not AGENT_RE.fullmatch(item) for item in agents):
        print("Invalid --agents list.", file=sys.stderr)
        return 2

    if not DISAGREEMENTS_DIR.exists():
        return 0
    if not DISAGREEMENTS_DIR.is_dir():
        print("Disagreements path is not a directory.", file=sys.stderr)
        return 2

    records = sorted(DISAGREEMENTS_DIR.glob(f"{args.story}-*.md"))
    unresolved = False
    for path in records:
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            print(f"Cannot read disagreement record: {path.name}", file=sys.stderr)
            return 2
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            print(f"Invalid JSON in disagreement record: {path.name}", file=sys.stderr)
            return 2
        if not _has_human_decision(record):
            unresolved = True

    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
