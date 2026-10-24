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

    def run_detector(self):
        with patch.object(detect_conflict, "DISAGREEMENTS_DIR", self.disagreements_dir):
            return detect_conflict.main(self.args)

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
