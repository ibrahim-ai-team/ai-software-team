"""Tests for append-only, secret-conscious persistent lessons."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import add_lesson


class AddLessonTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.lessons_path = Path(self.temp_dir.name) / "lessons.md"
        self.lessons_path.write_text("# Lessons\n", encoding="utf-8")
        self.valid = [
            "--title",
            "Validate gate evidence",
            "--context",
            "A delivery gate was evaluated",
            "--error",
            "The result was accepted without complete evidence",
            "--rule",
            "Check every required result before proceeding",
            "--story",
            "SHOP-12",
        ]

    def run_writer(self, args=None):
        with patch.object(add_lesson, "LESSONS_PATH", self.lessons_path):
            return add_lesson.main(self.valid if args is None else args)

    def test_first_lesson_gets_l001(self):
        self.assertEqual(self.run_writer(), 0)
        self.assertIn("## L001 — Validate gate evidence", self.lessons_path.read_text())

    def test_second_lesson_gets_l002(self):
        self.assertEqual(self.run_writer(), 0)
        self.assertEqual(self.run_writer(), 0)
        content = self.lessons_path.read_text()
        self.assertIn("## L001 — Validate gate evidence", content)
        self.assertIn("## L002 — Validate gate evidence", content)

    def test_empty_field_returns_one_without_write(self):
        args = self.valid.copy()
        args[1] = " "
        before = self.lessons_path.read_bytes()
        self.assertEqual(self.run_writer(args), 1)
        self.assertEqual(self.lessons_path.read_bytes(), before)

    def test_suspicious_token_term_returns_one(self):
        args = self.valid.copy()
        args[1] = "token handling lesson"
        before = self.lessons_path.read_bytes()
        self.assertEqual(self.run_writer(args), 1)
        self.assertEqual(self.lessons_path.read_bytes(), before)

    def test_password_and_secret_markers_are_rejected(self):
        for marker in ("password", "secret"):
            with self.subTest(marker=marker):
                args = self.valid.copy()
                args[3] = f"Failure involved {marker} values"
                before = self.lessons_path.read_bytes()
                self.assertEqual(self.run_writer(args), 1)
                self.assertEqual(self.lessons_path.read_bytes(), before)

    def test_existing_content_is_never_truncated(self):
        original = "# Existing lessons\n\n## L007 — Preserve history\n\n- **Rule to apply:** Keep prior lessons.\n"
        self.lessons_path.write_text(original, encoding="utf-8")
        self.assertEqual(self.run_writer(), 0)
        content = self.lessons_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith(original))
        self.assertIn("## L008 — Validate gate evidence", content)

    def test_story_is_required_by_cli(self):
        args = self.valid[:-2]
        self.assertEqual(self.run_writer(args), 2)

    def test_no_deletion_or_truncation_mode_is_exposed(self):
        source = Path(add_lesson.__file__).read_text(encoding="utf-8")
        self.assertNotIn("unlink(", source)
        self.assertNotIn("truncate(", source)
        self.assertNotIn('"w"', source)
        self.assertNotIn("'w'", source)

    def test_appends_date_and_source_story(self):
        self.assertEqual(self.run_writer(), 0)
        content = self.lessons_path.read_text(encoding="utf-8")
        self.assertIn("- **Date:** ", content)
        self.assertIn("- **Source story:** SHOP-12", content)


if __name__ == "__main__":
    unittest.main()
