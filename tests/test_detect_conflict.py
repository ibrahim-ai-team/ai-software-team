"""Tests for the read-only conflict detector."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import detect_conflict


class DetectConflictTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.disagreements_dir = Path(self.temp_dir.name)
        self.args = ["--story", "US-123", "--agents", "software-architect,tech-lead"]

    def run_detector(self, approvers=None):
        # Isolated from the repository's real .claude/human-approvers.json.
        approvers_path = Path(self.temp_dir.name) / "approvers.json"
        if approvers is not None:
            approvers_path.write_text(approvers, encoding="utf-8")
        with (
            patch.object(detect_conflict, "DISAGREEMENTS_DIR", self.disagreements_dir),
            patch.object(detect_conflict, "APPROVERS_PATH", approvers_path),
        ):
            return detect_conflict.main(self.args)

    def decision(self, decided_by):
        self.write_record(
            json.dumps({"story": "US-123", "human_decision": {"decided_by": decided_by, "decision": "Use a monolith."}})
        )

    def test_decided_by_must_match_exactly(self):
        for value in ("not human", "agent pretending to be human", "software-architect", "sponsor's agent"):
            with self.subTest(decided_by=value):
                self.decision(value)
                self.assertEqual(self.run_detector(), 1)

    def test_configured_approvers_replace_generic_names(self):
        self.decision("ibrahim-ghorafi")
        self.assertEqual(self.run_detector(approvers='{"approvers": ["Ibrahim-Ghorafi"]}'), 0)
        self.decision("human sponsor")
        self.assertEqual(self.run_detector(approvers='{"approvers": ["ibrahim-ghorafi"]}'), 1)
        self.assertEqual(self.run_detector(approvers="{"), 1)

    def write_record(self, content, name="US-123-architecture.md"):
        (self.disagreements_dir / name).write_text(content, encoding="utf-8")

    def test_no_disagreement_file_returns_zero(self):
        self.assertEqual(self.run_detector(), 0)

    def test_record_without_human_decision_returns_one(self):
        self.write_record(json.dumps({"story": "US-123", "human_decision": None}))
        self.assertEqual(self.run_detector(), 1)

    def test_record_with_human_decision_returns_zero(self):
        self.write_record(
            json.dumps(
                {
                    "story": "US-123",
                    "human_decision": {
                        "decided_by": "human sponsor",
                        "decision": "Use a modular monolith.",
                    },
                }
            )
        )
        self.assertEqual(self.run_detector(), 0)

    def test_invalid_json_returns_two(self):
        self.write_record("{")
        self.assertEqual(self.run_detector(), 2)


if __name__ == "__main__":
    unittest.main()
