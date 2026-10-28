"""Progressive disclosure: short always-loaded summaries, complete detail one link away."""

import re
import unittest
from pathlib import Path

from scripts.check_markdown_links import find_broken_links, github_slug

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "workflows" / "orchestration-contract.md"
PROCEDURES = ROOT / "workflows" / "orchestration-procedures.md"
ORCHESTRATOR = ROOT / ".claude" / "agents" / "agile-orchestrator.md"
CLAUDE_MD = ROOT / ".claude" / "CLAUDE.md"


def sections(path):
    return [line[3:].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("## ")]


class ProgressiveDisclosureTests(unittest.TestCase):
    def test_every_procedure_is_reachable_from_the_contract_and_its_index(self):
        contract = CONTRACT.read_text(encoding="utf-8")
        procedures = PROCEDURES.read_text(encoding="utf-8")
        for title in sections(PROCEDURES):
            if title == "Contents":
                continue
            anchor = github_slug(title)
            with self.subTest(section=title):
                self.assertIn(f"orchestration-procedures.md#{anchor}", contract)
                self.assertIn(f"](#{anchor})", procedures.split("## Contents", 1)[1].split("\n## ", 1)[0])

    def test_every_link_and_anchor_in_the_repository_resolves(self):
        # Summaries are only useful if every pointer to the detail still lands on a real file and heading.
        self.assertEqual(find_broken_links(ROOT), [])

    def test_procedures_link_only_back_to_the_contract(self):
        # References stay one level deep: the procedures file must not send readers to further procedure files.
        links = re.findall(r"\]\(([^)#]+)", PROCEDURES.read_text(encoding="utf-8"))
        self.assertEqual([link for link in links if link.endswith(".md")], [])

    def test_contract_keeps_every_rule_inline(self):
        # Each moved procedure leaves its obligation in the always-read contract, not only behind a link.
        contract = CONTRACT.read_text(encoding="utf-8")
        for rule in (
            "never coordinate while another live lock is held",
            "never reassign a row that is still active",
            "call `scripts/add_lesson.py` before retrying",
            "never set Done without a verified human-merged PR",
            "needs a documented threat model before implementation",
            "acceptance checklist",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, contract)

    def test_skills_are_hidden_from_context_but_routable(self):
        orchestrator = ORCHESTRATOR.read_text(encoding="utf-8")
        for skill in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            frontmatter = text.split("---", 2)[1]
            with self.subTest(skill=skill.parent.name):
                self.assertIn("disable-model-invocation: true", frontmatter)
                self.assertIn(skill.relative_to(ROOT).as_posix(), orchestrator)

    def test_essential_rules_stay_in_always_loaded_context(self):
        # CLAUDE.md loads into every session and subagent; the orchestrator body is the main session's prompt.
        claude_md = CLAUDE_MD.read_text(encoding="utf-8")
        for rule in ("never work directly on `main`", "Never place credentials/tokens/secrets", "Lessons are binding"):
            with self.subTest(rule=rule):
                self.assertIn(rule.lower(), claude_md.lower())
        orchestrator = ORCHESTRATOR.read_text(encoding="utf-8")
        for command in ("detect_conflict.py", "check_approvals.py", "check_gates.py", "relevant_lessons.py"):
            with self.subTest(command=command):
                self.assertIn(command, orchestrator)


if __name__ == "__main__":
    unittest.main()
