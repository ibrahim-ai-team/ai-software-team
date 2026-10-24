"""Print a bounded set of lessons relevant to one story (standard library only)."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS_PATH = ROOT / ".claude" / "lessons" / "lessons.md"
NO_LESSONS = "Aucune leçon applicable pour cette story"


def _sections(text: str) -> list[str]:
    matches = list(re.finditer(r"(?m)^##\s+(L\d+)\s+—\s+(.+?)\s*$", text))
    return [
        text[m.start() : (matches[i + 1].start() if i + 1 < len(matches) else len(text))].strip() for i, m in enumerate(matches)
    ]


def _field(section: str, name: str) -> str:
    match = re.search(rf"(?im)^\s*-\s*\*\*{re.escape(name)}:\*\*\s*(.*?)\s*$", section)
    return match.group(1).strip() if match else ""


def _tokens(value: str) -> set[str]:
    return {part.casefold() for part in re.findall(r"[A-Za-z0-9]+", value) if part}


def _score(section: str, story: str) -> tuple[int, int, str]:
    folded = story.casefold()
    source, tags = _field(section, "Source story").casefold(), _field(section, "Tags").casefold()
    title = section.splitlines()[0].casefold()
    exact = folded in source or folded in tags or folded in title
    tagged = bool(_tokens(story) & _tokens(tags))
    try:
        recent = date.fromisoformat(_field(section, "Date")).toordinal()
    except ValueError:
        recent = 0
    return (2 if exact else int(tagged), recent, title)


def select_lessons(story: str, maximum: int = 5, lessons_path: Path | None = None) -> list[str]:
    """Return at most maximum matching lessons; missing files fail safe."""
    if maximum < 1:
        return []
    try:
        text = (lessons_path or LESSONS_PATH).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    selected = []
    folded = story.casefold()
    story_tokens = _tokens(story)
    for section in _sections(text):
        source, tags = _field(section, "Source story").casefold(), _field(section, "Tags").casefold()
        title = section.splitlines()[0].casefold()
        if folded in source or folded in tags or folded in title or story_tokens & _tokens(tags):
            selected.append(section)
    selected.sort(key=lambda item: _score(item, story), reverse=True)
    return selected[:maximum]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", required=True, help="Story ID, e.g. SHOP-12")
    parser.add_argument("--max", type=int, default=5, dest="maximum", help="Maximum lessons (default: 5)")
    args = parser.parse_args()
    if args.maximum < 1:
        parser.error("--max must be at least 1")
    lessons = select_lessons(args.story, args.maximum)
    print("\n\n".join(lessons) if lessons else NO_LESSONS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

