"""Tests for the read-only human approval checker."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_approvals


class CheckApprovalsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.approvals_dir = Path(self.temp_dir.name)
        self.approval_path = self.approvals_dir / "CP1-SHOP-12.json"
        self.record = {
            "checkpoint": "CP1",
            "story": "SHOP-12",
            "approved_by": "human-reviewer",
            "date": "2026-10-24T12:00:00Z",
            "artifact_hash": "a" * 64,
        }
        self.write_record()

    def write_record(self):
        self.approval_path.write_text(json.dumps(self.record), encoding="utf-8")

    def run_checker(self, *argv):
        with patch.object(check_approvals, "APPROVALS_DIR", self.approvals_dir):
            return check_approvals.main(list(argv))

    def test_valid_approval_returns_zero(self):
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--checkpoint", "CP1"), 0)

    def test_missing_approval_returns_one(self):
        self.approval_path.unlink()
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--checkpoint", "CP1"), 1)

    def test_invalid_json_returns_one(self):
        self.approval_path.write_text("{", encoding="utf-8")
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--checkpoint", "CP1"), 1)

    def test_invalid_hash_returns_one(self):
        self.record["artifact_hash"] = "not-a-sha256"
        self.write_record()
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--checkpoint", "CP1"), 1)

    def test_missing_required_arguments_returns_two(self):
        self.assertEqual(self.run_checker("--story", "SHOP-12"), 2)
        self.assertEqual(self.run_checker("--checkpoint", "CP1"), 2)

    def test_story_and_checkpoint_must_match(self):
        self.assertEqual(self.run_checker("--story", "OTHER-1", "--checkpoint", "CP1"), 1)
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--checkpoint", "CP2"), 1)

    def test_invalid_date_returns_one(self):
        self.record["date"] = "yesterday"
        self.write_record()
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--checkpoint", "CP1"), 1)

    def test_checker_does_not_modify_approval_file(self):
        before = self.approval_path.read_bytes()
        self.run_checker("--story", "SHOP-12", "--checkpoint", "CP1")
        self.assertEqual(self.approval_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
