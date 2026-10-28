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

    def test_anchors_must_match_a_heading(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "guide.md").write_text(
                "# Guide\n\n## Claim protocol\n\n## Product Owner — brief\n\n```\n## Not a heading\n```\n## Dup\n\n## Dup\n",
                encoding="utf-8",
            )
            good = (
                "[a](guide.md#claim-protocol) [b](guide.md#product-owner--brief) [c](guide.md#dup-1) `guide.md#claim-protocol`\n"
            )
            (root / "README.md").write_text(good, encoding="utf-8")
            self.assertEqual(find_broken_links(root), [])
            (root / "README.md").write_text("[a](guide.md#renamed)\n`guide.md#not-a-heading`\n[c](#nowhere)\n", encoding="utf-8")
            errors = find_broken_links(root)
            self.assertEqual(len(errors), 3, errors)
            self.assertTrue(all("missing heading anchor" in error for error in errors), errors)

    def test_backticked_anchor_to_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("See `workflows/gone.md#section`.\n", encoding="utf-8")
            self.assertTrue(any("missing referenced file" in error for error in find_broken_links(root)))

    def test_rejects_links_that_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("[outside](../outside.md)\n", encoding="utf-8")
            errors = find_broken_links(root)
            self.assertTrue(any("escapes repository" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
