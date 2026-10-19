import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_cross_references import check
from scripts.check_placeholders import find_placeholders

ROOT = Path(__file__).resolve().parents[1]


class PlaceholderTests(unittest.TestCase):
    def scan(self, files: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, content in files.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(content, encoding="utf-8")
            return find_placeholders([root], root)

    def test_reports_field_and_table_placeholders_with_line(self):
        errors = self.scan({"docs/sprint.md": "# Sprint\n- Sprint goal: TBD\n**Priority:** TODO\n| Owner | TBD |\n"})
        self.assertEqual(len(errors), 3)
        self.assertIn("docs/sprint.md:2", errors[0])

    def test_skips_templates(self):
        self.assertEqual(self.scan({"templates/sprint-plan-template.md": "- Sprint goal: TBD\n"}), [])

    def test_allows_tracked_deferral_prose_and_code(self):
        content = ("- Estimate: TBD (refine in #12)\n- Dates: TBD by 2026-11-01\n"
                   "Mark it TBD with a refinement task.\n```\nOwner: TBD\n```\n")
        self.assertEqual(self.scan({"docs/plan.md": content}), [])

    def test_repository_has_no_unresolved_placeholders(self):
        self.assertEqual(find_placeholders([ROOT]), [])


class CrossReferenceTests(unittest.TestCase):
    def mutated(self, relative: str, old: str, new: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "repo"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            path = target / relative
            text = path.read_text(encoding="utf-8")
            self.assertIn(old, text)
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            return check(target)

    def test_repository_passes(self):
        self.assertEqual(check(ROOT), [])

    def test_rejects_unknown_agent_reference_with_line(self):
        errors = self.mutated(".claude/commands/plan-sprint.md", "`project-manager`", "`project-managr`")
        self.assertTrue(any("plan-sprint.md:" in e and "project-managr" in e for e in errors), errors)

    def test_rejects_missing_path_reference(self):
        errors = self.mutated(".claude/commands/kickoff.md", "`workflows/project-bootstrap.md`", "`workflows/missing.md`")
        self.assertTrue(any("missing referenced path 'workflows/missing.md'" in e for e in errors), errors)

    def test_rejects_name_mismatch_unknown_key_and_model(self):
        relative = ".claude/agents/business-analyst.md"
        self.assertTrue(any("does not match file name" in e for e in
                            self.mutated(relative, "name: business-analyst", "name: analyst")))
        self.assertTrue(any("unknown frontmatter key 'color'" in e for e in
                            self.mutated(relative, "name: business-analyst", "name: business-analyst\ncolor: blue")))
        self.assertTrue(any("model 'gpt-x'" in e for e in
                            self.mutated(relative, "name: business-analyst", "name: business-analyst\nmodel: gpt-x")))


if __name__ == "__main__":
    unittest.main()
