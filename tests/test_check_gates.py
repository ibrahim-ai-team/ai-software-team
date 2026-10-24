"""Tests for the read-only G1/G2 validation gate checker."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_gates


class CheckGatesTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.gates_dir = Path(self.temp_dir.name)
        self.g1_path = self.gates_dir / "G1-SHOP-12.json"
        self.g2_path = self.gates_dir / "G2-SHOP-12.json"
        self.g1 = {
            "passed": True,
            "reviewer": "code-review-security",
            "date": "2026-10-24T12:00:00Z",
            "plan_hash": "a" * 64,
        }
        self.g2 = {
            "passed": True,
            "reviewer": "code-review-security",
            "date": "2026-10-24T12:30:00Z",
            "checks": {"lint": "pass", "tests": "pass", "secrets": "pass"},
        }
        self.write(self.g1_path, self.g1)
        self.write(self.g2_path, self.g2)

    @staticmethod
    def write(path, record):
        path.write_text(json.dumps(record), encoding="utf-8")

    def run_checker(self, *argv):
        with patch.object(check_gates, "GATES_DIR", self.gates_dir):
            return check_gates.main(list(argv))

    def test_valid_g1_returns_zero(self):
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G1"), 0)

    def test_absent_g1_returns_one(self):
        self.g1_path.unlink()
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G1"), 1)

    def test_invalid_plan_hash_returns_one(self):
        self.g1["plan_hash"] = "not-a-hash"
        self.write(self.g1_path, self.g1)
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G1"), 1)

    def test_g2_lint_failure_returns_one(self):
        self.g2["checks"]["lint"] = "fail"
        self.write(self.g2_path, self.g2)
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G2"), 1)

    def test_complete_g2_returns_zero(self):
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G2"), 0)

    def test_invalid_gate_returns_two(self):
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G3"), 2)

    def test_missing_required_argument_returns_two(self):
        self.assertEqual(self.run_checker("--story", "SHOP-12"), 2)
        self.assertEqual(self.run_checker("--gate", "G1"), 2)

    def test_g2_missing_test_or_secret_result_returns_one(self):
        for key in ("tests", "secrets"):
            with self.subTest(key=key):
                self.g2["checks"].pop(key)
                self.write(self.g2_path, self.g2)
                self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G2"), 1)
                self.g2["checks"][key] = "pass"

    def test_checker_never_modifies_gate_files(self):
        before = {p.name: p.read_bytes() for p in self.gates_dir.iterdir()}
        self.run_checker("--story", "SHOP-12", "--gate", "G1")
        self.run_checker("--story", "SHOP-12", "--gate", "G2")
        after = {p.name: p.read_bytes() for p in self.gates_dir.iterdir()}
        self.assertEqual(before, after)

    def test_rejects_false_pass_and_wrong_reviewer(self):
        self.g1["passed"] = False
        self.write(self.g1_path, self.g1)
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G1"), 1)
        self.g1["passed"] = True
        self.g1["reviewer"] = "another-agent"
        self.write(self.g1_path, self.g1)
        self.assertEqual(self.run_checker("--story", "SHOP-12", "--gate", "G1"), 1)


if __name__ == "__main__":
    unittest.main()
