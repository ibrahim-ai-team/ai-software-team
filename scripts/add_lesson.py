#!/usr/bin/env python3
"""Append a sanitized, numbered lesson to the persistent lessons file."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS_PATH = ROOT / ".claude" / "lessons" / "lessons.md"
LESSON_ID_PATTERN = re.compile(r"(?m)^## L(\d{3,})\s+—")
SUSPICIOUS_TERMS = ("token", "password", "secret")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--error", required=True)
    parser.add_argument("--rule", required=True)
    parser.add_argument("--story", required=True)
    return parser.parse_args(argv)


def validate_fields(values: dict[str, str]) -> tuple[bool, str]:
    for name, value in values.items():
        if not value.strip():
            return False, f"{name} must not be empty"
        if any(term in value.casefold() for term in SUSPICIOUS_TERMS):
            return False, f"{name} contains a prohibited sensitive-term marker"
        if "\x00" in value:
            return False, f"{name} contains an invalid control character"
    return True, ""


def next_lesson_id(existing: str) -> str:
    numbers = [int(match) for match in LESSON_ID_PATTERN.findall(existing)]
    return f"L{max(numbers, default=0) + 1:03d}"


def render_lesson(
    lesson_id: str, title: str, context: str, error: str, rule: str, story: str
) -> str:
    safe_title = " ".join(title.split())
    return (
        f"\n## {lesson_id} — {safe_title}\n\n"
        f"- **Context:** {' '.join(context.split())}\n"
        f"- **Observed error:** {' '.join(error.split())}\n"
        f"- **Rule to apply:** {' '.join(rule.split())}\n"
        f"- **Date:** {date.today().isoformat()}\n"
        f"- **Source story:** {' '.join(story.split())}\n"
    )


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    values = {
        "title": args.title,
        "context": args.context,
        "error": args.error,
        "rule": args.rule,
        "story": args.story,
    }
    valid, reason = validate_fields(values)
    if not valid:
        print(f"ERROR: lesson rejected; {reason}.", file=sys.stderr)
        return 1

    try:
        existing = LESSONS_PATH.read_text(encoding="utf-8") if LESSONS_PATH.exists() else ""
        lesson_id = next_lesson_id(existing)
        rendered = render_lesson(lesson_id, **values)
        LESSONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LESSONS_PATH.open("a", encoding="utf-8", newline="\n") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(rendered)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: unable to append lesson ({exc.__class__.__name__}).", file=sys.stderr)
        return 1

    print(f"Added {lesson_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
