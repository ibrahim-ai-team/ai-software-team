"""Regression tests for scripts/check_governance.py.

The API Quiz scenarios below are SIMULATIONS built from offline fixtures that
copy the shape of records and files seen in ibrahim-ai-team/api-quiz-app. They
exercise the checker's decisions; they do not prove live GitHub or Claude Code
behaviour.
"""

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_governance import check_pr_body, check_release, check_sprints

ROOT = Path(__file__).resolve().parents[1]
DAY = dt.date(2026, 11, 15)


def sprint_record(
    sprint_id="S2",
    status="Active",
    start="2026-11-09",
    end="2026-11-22",
    approved="SD-S2 sponsor 2026-11-08",
    capacity="10",
    committed=(),
    changes=(),
    created=(),
    review=None,
):
    lines = [
        "# Sprint record",
        "## Sprint",
        f"- Sprint ID: {sprint_id}",
        f"- Start: {start}",
        f"- End: {end}",
        f"- Status: {status}",
        "- Goal: A learner completes one reviewed 10-question quiz on a phone",
        f"- Approved by: {approved}",
        "- Membership source: this file only (no GitHub sprint field configured)",
        f"- Capacity (points): {capacity}",
        "## Committed issues",
        "| Issue | Title | Priority | Points | Added by | Status | PR | Evidence | Next |",
        "|---|---|---|---|---|---|---|---|---|",
        *committed,
        "## Scope changes",
        "| ID | Date | Issue | Change | Reason | Displaces | Decision | Decided by |",
        "|---|---|---|---|---|---|---|---|",
        *changes,
        "## Issue creation log",
        "| Issue | Problem | Duplicate search | Result | Target | Why now |",
        "|---|---|---|---|---|---|",
        *created,
    ]
    if review is not None:
        lines += ["## Sprint review", f"- Goal met: {review[0]}", f"- Evidence: {review[1]}"]
    return "\n".join(lines) + "\n"


def item(issue, status="In Progress", points=3, added="plan", pr="-", evidence="-", nxt="-"):
    return f"| {issue} | story | P1 | {points} | {added} | {status} | {pr} | {evidence} | {nxt} |"


class GovernanceCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def sprints(self, *texts, as_of=DAY):
        paths = [self.write(f"sprint-{i}.md", text) for i, text in enumerate(texts)]
        return check_sprints(paths, as_of)

    def assertCode(self, errors, code, fragment=""):
        self.assertTrue(any(code in e and fragment in e for e in errors), errors)


class SprintRecordTests(GovernanceCase):
    def test_complete_active_sprint_passes(self):
        self.assertEqual(self.sprints(sprint_record(committed=[item("#9"), item("#10")])), [])

    def test_missing_dates_and_approval_are_rejected(self):
        errors = self.sprints(sprint_record(start="TBD", approved="not approved"))
        self.assertCode(errors, "G03")
        self.assertCode(errors, "G05")

    def test_capacity_is_enforced(self):
        errors = self.sprints(sprint_record(committed=[item("#9", points=8), item("#10", points=5)]))
        self.assertCode(errors, "G15", "exceed capacity 10")

    def test_duplicate_sprint_ids_are_rejected(self):
        errors = self.sprints(sprint_record(status="Closed", review=("yes", "run 1")), sprint_record())
        self.assertCode(errors, "G01", "also used by")


class ApiQuizScenarioTests(GovernanceCase):
    """Phase 9 scenarios (simulated, offline)."""

    def test_1_duplicate_issue_is_rejected(self):
        # The creation check found #13 (US-8) but the issue was created anyway.
        created = ["| #120 | more questions | searched 'question bank' -> #13 | duplicate of #13 | backlog | none |"]
        errors = self.sprints(sprint_record(committed=[item("#9")], created=created))
        self.assertCode(errors, "G12", "link the existing issue instead")
        # An issue with no recorded search, like #88, is also rejected.
        created = ["| #88 | CI image | - | new | backlog | flaky E2E |"]
        self.assertCode(self.sprints(sprint_record(created=created)), "G12", "no recorded duplicate search")
        # The correct outcome: not created, existing issue linked.
        created = ["| - | more questions | searched 'question bank' -> #13 | duplicate of #13 | backlog | none |"]
        self.assertEqual(self.sprints(sprint_record(committed=[item("#9")], created=created)), [])

    def test_2_optional_feature_stays_outside_approved_sprint(self):
        optional = item("#121", status="Ready", points=2, added="orchestrator")
        errors = self.sprints(sprint_record(committed=[item("#9"), optional]))
        self.assertCode(errors, "G07", "not by the approved plan or a recorded scope change")
        proposed = ["| SC-1 | 2026-11-12 | #121 | add | nice to have | nothing | proposed | - |"]
        errors = self.sprints(sprint_record(committed=[item("#9"), item("#121", added="SC-1")], changes=proposed))
        self.assertCode(errors, "G07", "not approved by a named decision owner")
        created = ["| #121 | share score | searched 'share' -> none | new | S2 | sponsor idea |"]
        self.assertCode(self.sprints(sprint_record(committed=[item("#9")], created=created)), "G12", "not in Committed issues")
        # Correct outcome: the new idea goes to the product backlog.
        created = ["| #121 | share score | searched 'share' -> none | new | backlog | sponsor idea, not in MVP |"]
        self.assertEqual(self.sprints(sprint_record(committed=[item("#9")], created=created)), [])

    def test_2b_urgent_work_enters_only_through_an_approved_scope_change(self):
        change = [
            "| SC-1 | 2026-11-12 | #122 | add | production defect | #10 (3 points) to backlog | approved | sponsor 2026-11-12 |"
        ]
        committed = [item("#9"), item("#10", status="Not done", nxt="backlog (displaced by SC-1)"), item("#122", added="SC-1")]
        self.assertEqual(self.sprints(sprint_record(committed=committed, changes=change)), [])
        change = ["| SC-1 | 2026-11-12 | #122 | add | production defect | - | approved | sponsor 2026-11-12 |"]
        self.assertCode(self.sprints(sprint_record(committed=committed, changes=change)), "G07", "what it displaces")

    def test_4_task_is_not_complete_without_evidence(self):
        for pr, evidence in (("-", "agent reported done"), ("#114", "PR opened, CI green"), ("#114", "-")):
            with self.subTest(pr=pr, evidence=evidence):
                errors = self.sprints(sprint_record(committed=[item("#12", status="Done", pr=pr, evidence=evidence)]))
                self.assertCode(errors, "G08")
        done = item(
            "#12", status="Done", pr="#114", evidence="merged 2026-11-14 by owner; CI run 123 green; AC US-6.1-6.4 checked"
        )
        self.assertEqual(self.sprints(sprint_record(committed=[done])), [])

    def test_5_blocked_task_does_not_extend_the_sprint(self):
        blocked = item("#39", status="Blocked", nxt="sponsor: environment branch rule")
        self.assertEqual(self.sprints(sprint_record(committed=[blocked])), [])
        self.assertCode(self.sprints(sprint_record(committed=[item("#39", status="Blocked")])), "G09")
        errors = self.sprints(sprint_record(committed=[blocked]), as_of=dt.date(2026, 11, 30))
        self.assertCode(errors, "G10", "close it, do not extend it")

    def test_6_sprint_closes_with_incomplete_work_accounted_for(self):
        review = ("partial", "sprint review 2026-11-22: 2 of 3 stories merged")
        committed = [
            item("#9", status="Done", pr="#72", evidence="merged; E2E run 99 green"),
            item("#11", status="In Progress"),
            item("#39", status="Blocked", nxt="sponsor decision"),
        ]
        errors = self.sprints(sprint_record(status="Closed", committed=committed, review=review))
        self.assertCode(errors, "G11", "#11")
        committed[1] = item("#11", status="Not done", nxt="")
        self.assertCode(self.sprints(sprint_record(status="Closed", committed=committed, review=review)), "G11", "disposition")
        committed[1] = item("#11", status="Not done", nxt="candidate S3; re-estimate first")
        self.assertEqual(self.sprints(sprint_record(status="Closed", committed=committed, review=review)), [])
        self.assertCode(self.sprints(sprint_record(status="Closed", committed=committed)), "G11", "Goal met")

    def test_7_next_sprint_is_replanned_not_auto_carried(self):
        review = ("partial", "review 2026-11-22")
        s2 = sprint_record(
            status="Closed",
            review=review,
            committed=[
                item("#11", status="Not done", points=5, nxt="candidate S3"),
                item("#12", status="Not done", points=5, nxt="backlog: re-estimated 14"),
            ],
        )
        s3_args = {"sprint_id": "S3", "start": "2026-11-23", "end": "2026-12-06", "approved": "SD-S3 sponsor 2026-11-22"}
        carried_everything = sprint_record(**s3_args, committed=[item("#11", points=5), item("#12", points=14)])
        self.assertCode(self.sprints(s2, carried_everything, as_of=dt.date(2026, 11, 24)), "G15")
        unapproved = sprint_record(**{**s3_args, "approved": "not approved"}, committed=[item("#11", points=5)])
        self.assertCode(self.sprints(s2, unapproved, as_of=dt.date(2026, 11, 24)), "G05")
        s2_open = sprint_record(committed=[item("#11", points=5)])
        early = sprint_record(**s3_args, committed=[item("#11", points=5)])
        self.assertCode(self.sprints(s2_open, early, as_of=dt.date(2026, 11, 20)), "G14", "is not Closed")
        replanned = sprint_record(**s3_args, committed=[item("#11", points=5), item("#17", points=3)])
        self.assertEqual(self.sprints(s2, replanned, as_of=dt.date(2026, 11, 24)), [])


class ReleaseCriteriaTests(GovernanceCase):
    """Scenario 3: the 24-question MVP decision against the older 60-question requirement."""

    RULES_TS = (
        "export const RELEASE_THRESHOLDS = {\n  minReviewedQuestions: 60,\n  minTopics: 8,\n  minPerTopic: 5,\n} as const;\n"
    )
    DEPLOY = (
        "on:\n  workflow_dispatch:\n    inputs:\n"
        "      accept_below_release_thresholds:\n        type: boolean\n        default: false\n"
    )

    def state(self, conflicts=()):
        rows = [
            "| RC-1 | minReviewedQuestions | 24 | SD-REL-01 | scripts/content/rules.ts: minReviewedQuestions: {value} |",
            "| RC-2 | minTopics | 3 | SD-REL-01 | scripts/content/rules.ts: minTopics: {value} |",
        ]
        return self.write(
            "state.md",
            "\n".join(
                [
                    "# Project state",
                    "## Release criteria",
                    "| ID | Criterion | Value | Decision | Mirrors |",
                    "|---|---|---|---|---|",
                    *rows,
                    "## Requirement conflicts",
                    "| ID | Criterion | Sources | Status | Decision needed |",
                    "|---|---|---|---|---|",
                    *conflicts,
                ]
            )
            + "\n",
        )

    def repo(self, rules=RULES_TS, deploy=DEPLOY):
        root = self.dir / "app"
        (root / "scripts/content").mkdir(parents=True, exist_ok=True)
        (root / "scripts/content/rules.ts").write_text(rules, encoding="utf-8")
        (root / ".github/workflows").mkdir(parents=True, exist_ok=True)
        (root / ".github/workflows/deploy-pages.yml").write_text(deploy, encoding="utf-8")
        return root

    def test_3_unrecorded_conflict_is_detected(self):
        errors, _ = check_release(self.state(), self.repo(), release=False)
        self.assertCode(errors, "G21", "approved value 24 but scripts/content/rules.ts says 60")
        self.assertCode(errors, "unrecorded requirement conflict")

    def test_3_recorded_conflict_is_surfaced_and_blocks_release(self):
        conflicts = [
            "| RC-C1 | minReviewedQuestions | SD-REL-01 (24) vs US-8.1 (60) | open | sponsor: confirm 24 and move 60 to future |",
            "| RC-C2 | minTopics | SD-REL-01 (3) vs US-8.1 (8) | open | same decision |",
        ]
        errors, notes = check_release(self.state(conflicts), self.repo(), release=False)
        self.assertEqual(errors, [])
        self.assertEqual(len(notes), 2, notes)
        errors, _ = check_release(self.state(conflicts), self.repo(), release=True)
        self.assertCode(errors, "G22", "open requirement conflict on 'minReviewedQuestions'")

    def test_3_release_bypass_input_blocks_release(self):
        aligned = self.RULES_TS.replace("60", "24").replace("minTopics: 8", "minTopics: 3")
        errors, _ = check_release(self.state(), self.repo(rules=aligned), release=True)
        self.assertCode(errors, "G22", "accept_below_release_thresholds")
        errors, _ = check_release(self.state(), self.repo(rules=aligned, deploy="on:\n  workflow_dispatch:\n"), release=True)
        self.assertEqual(errors, [])

    def test_missing_mirror_file_is_an_error(self):
        errors, _ = check_release(self.state(), self.dir / "missing", release=False)
        self.assertCode(errors, "G21", "file must exist")


class PullRequestTests(GovernanceCase):
    """Scenario 8: a traceable PR that leaves the merge to the human owner."""

    def test_8_pr_template_is_traceable_and_keeps_human_merge(self):
        template = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        body = template.replace("Closes #", "Closes #12").replace("Sprint: S<n> or none", "Sprint: S2")
        self.assertEqual(check_pr_body(self.write("pr.md", body)), [])
        self.assertCode(check_pr_body(self.write("bare.md", "Fixed it.\n")), "G30")
        self.assertCode(check_pr_body(self.write("auto.md", body + "\nAuto-merge enabled.\n")), "G31")
        no_owner = body.replace("Human owner will perform the final merge", "Merged")
        self.assertCode(check_pr_body(self.write("owner.md", no_owner)), "G31")

    def test_8_merge_remains_denied_to_agents(self):
        settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertIn("Bash(gh pr merge*)", settings["permissions"]["deny"])


class TemplateTests(GovernanceCase):
    def test_sprint_template_has_every_section_the_checker_reads(self):
        text = (ROOT / "templates/sprint-plan-template.md").read_text(encoding="utf-8").lower()
        for heading in ("## sprint", "## committed issues", "## scope changes", "## issue creation log", "## sprint review"):
            self.assertIn(heading, text)
        for field in (
            "sprint id:",
            "start:",
            "end:",
            "status:",
            "goal:",
            "approved by:",
            "membership source:",
            "capacity (points):",
        ):
            self.assertIn(field, text)

    def test_project_state_template_has_release_sections(self):
        text = (ROOT / "templates/project-state-template.md").read_text(encoding="utf-8").lower()
        self.assertIn("## release criteria", text)
        self.assertIn("## requirement conflicts", text)


if __name__ == "__main__":
    unittest.main()
