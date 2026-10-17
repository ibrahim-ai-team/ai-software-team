import tempfile
import unittest
from pathlib import Path

from scripts.check_markdown_links import find_broken_links


class MarkdownLinkTests(unittest.TestCase):
    def test_reports_missing_local_link_with_line(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("[missing](docs/nope.md)\n", encoding="utf-8")
            errors = find_broken_links(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("README.md:1", errors[0])
            self.assertIn("docs/nope.md", errors[0])

    def test_accepts_existing_relative_and_external_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "README.md").write_text("[guide](docs/guide.md) [web](https://example.com)\n", encoding="utf-8")
            self.assertEqual(find_broken_links(root), [])

    def test_rejects_links_that_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("[outside](../outside.md)\n", encoding="utf-8")
            errors = find_broken_links(root)
            self.assertTrue(any("escapes repository" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
