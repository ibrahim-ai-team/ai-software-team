import shutil
import subprocess
import sys
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
        self.assertTrue(any("unknown frontmatter key 'colour'" in e for e in
                            self.mutated(relative, "name: business-analyst", "name: business-analyst\ncolour: blue")))
        self.assertTrue(any("model 'gpt-x'" in e for e in
                            self.mutated(relative, "name: business-analyst", "name: business-analyst\nmodel: gpt-x")))

    def test_accepts_documented_model_values(self):
        relative = ".claude/agents/business-analyst.md"
        for model in ("fable", "inherit", "claude-opus-5-5"):
            with self.subTest(model=model):
                self.assertEqual(self.mutated(relative, "name: business-analyst", f"name: business-analyst\nmodel: {model}"), [])

    def test_orchestrator_must_name_every_required_agent(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "repo"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            path = target / ".claude" / "agents" / "agile-orchestrator.md"
            path.write_text(path.read_text(encoding="utf-8").replace("`tech-lead`", "the lead"), encoding="utf-8")
            errors = [e for e in check(target) if "cannot delegate" in e]
        self.assertTrue(errors and "tech-lead" in errors[0], errors)


class OrchestrationContractTests(unittest.TestCase):
    """Static checks of the delegation model; they do not prove runtime behaviour."""

    def run_validator(self, relative: str, old: str, new: str):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "repo"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            path = target / relative
            if new is None:
                path.unlink()
            else:
                text = path.read_text(encoding="utf-8")
                self.assertIn(old, text)
                path.write_text(text.replace(old, new, 1), encoding="utf-8")
            return subprocess.run([sys.executable, "scripts/validate_team.py"], cwd=target,
                                  capture_output=True, text=True, check=False)

    def test_only_orchestrator_may_delegate(self):
        result = self.run_validator(".claude/agents/tech-lead.md", "tools: Read,", "tools: Agent, Read,")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Only agile-orchestrator may delegate", result.stdout)

    def test_orchestrator_needs_agent_tool(self):
        result = self.run_validator(".claude/agents/agile-orchestrator.md", "tools: Agent, Read,", "tools: Read,")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("must list the 'Agent' tool", result.stdout)

    def test_required_role_cannot_be_removed(self):
        result = self.run_validator(".claude/agents/tech-lead.md", "", None)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Missing required agent: .claude/agents/tech-lead.md", result.stdout)

    def test_tech_lead_cannot_regain_edit_tools(self):
        for tool in ("Edit", "Write", "Bash"):
            with self.subTest(tool=tool):
                result = self.run_validator(".claude/agents/tech-lead.md", "tools: Read, Grep, Glob",
                                            f"tools: Read, Grep, Glob, {tool}")
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("tech-lead must remain read-only", result.stdout)

    def test_tech_lead_allowlist_is_read_only(self):
        text = (ROOT / ".claude" / "agents" / "tech-lead.md").read_text(encoding="utf-8")
        tools = next(line for line in text.splitlines() if line.startswith("tools:"))
        self.assertEqual({t.strip() for t in tools.split(":", 1)[1].split(",")}, {"Read", "Grep", "Glob"})

    def test_ineffective_write_path_rules_are_rejected(self):
        result = self.run_validator(".claude/settings.json", '"Edit(./.claude/settings.json)",',
                                    '"Edit(./.claude/settings.json)", "Write(./docs/x.md)",')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("ineffective path rule Write(./docs/x.md)", result.stdout)

    def test_contract_names_tech_lead_and_human_merge(self):
        contract = (ROOT / "workflows" / "orchestration-contract.md").read_text(encoding="utf-8")
        self.assertNotIn("no separate Tech Lead agent", contract)
        self.assertIn("`tech-lead` reviews technical quality", contract)
        self.assertIn("Only the human repository owner merges PRs", contract)
        self.assertIn("two-week sprint", contract)


if __name__ == "__main__":
    unittest.main()
