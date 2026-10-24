"""Regression tests for bounded and fail-safe lesson selection."""

import tempfile
import unittest
from pathlib import Path

from scripts import relevant_lessons


def lesson(number, story="", tags="", day="2026-10-20"):
    return (
        f"## L{number:03d} — Lesson {number}\n\n"
        f"- **Context:** Example context.\n"
        f"- **Rule to apply:** Apply rule {number}.\n"
        f"- **Date:** {day}\n"
        f"- **Source story:** {story}\n"
        f"- **Tags:** {tags}\n"
    )


class RelevantLessonsTests(unittest.TestCase):
    def test_missing_file_is_fail_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            result = relevant_lessons.select_lessons("SHOP-12", 5, Path(directory) / "missing.md")
        self.assertEqual(result, [])

    def test_matches_source_story_case_insensitively(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lessons.md"
            path.write_text(lesson(1, story="shop-12"), encoding="utf-8")
            result = relevant_lessons.select_lessons("SHOP-12", 5, path)
        self.assertEqual(len(result), 1)
        self.assertIn("L001", result[0])

    def test_matches_story_tokens_in_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lessons.md"
            path.write_text(lesson(1, tags="SHOP, checkout"), encoding="utf-8")
            result = relevant_lessons.select_lessons("SHOP-12", 5, path)
        self.assertEqual(len(result), 1)

    def test_fifty_records_never_exceed_maximum(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lessons.md"
            content = "".join(
                lesson(i, story="SHOP-12" if i % 2 else "OTHER-1", day=f"2026-10-{(i % 28) + 1:02d}") for i in range(1, 51)
            )
            path.write_text(content, encoding="utf-8")
            result = relevant_lessons.select_lessons("SHOP-12", 5, path)
        self.assertEqual(len(result), 5)
        self.assertTrue(all("Source story:** SHOP-12" in item for item in result))

    def test_no_match_returns_empty_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lessons.md"
            path.write_text(lesson(1, story="OTHER-1", tags="database"), encoding="utf-8")
            self.assertEqual(relevant_lessons.select_lessons("SHOP-12", 5, path), [])

    def test_maximum_is_respected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lessons.md"
            path.write_text("".join(lesson(i, story="SHOP-12") for i in range(1, 8)), encoding="utf-8")
            self.assertEqual(len(relevant_lessons.select_lessons("SHOP-12", 2, path)), 2)


if __name__ == "__main__":
    unittest.main()

