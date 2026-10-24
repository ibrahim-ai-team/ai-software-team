"""Schema contract tests for the ci-verifier evidence response."""

import json
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = ROOT / ".claude" / "agents" / "ci-verifier.md"

REQUIRED_CHECKS = {"lint", "tests", "secrets"}
VALID_STATUSES = {"pass", "blocked"}


class CiVerifierSchemaTests(unittest.TestCase):
    def test_agent_contract_documents_schema_and_security_boundaries(self):
        text = AGENT_PATH.read_text(encoding="utf-8")
        for marker in (
            "tools: Read, Bash",
            "Closed command allowlist",
            "Explicitly forbidden",
            '"story": "SHOP-12"',
            '"gate": "G2"',
            '"overall": "pass"',
            '"skipped": true',
            "NEVER write to `.claude/gates/`",
        ):
            self.assertIn(marker, text)
        self.assertNotIn("tools: Read, Bash, Edit", text)
        self.assertNotIn("tools: Read, Bash, Write", text)

    def test_example_json_has_required_shape(self):
        example = {
            "story": "SHOP-12",
            "gate": "G2",
            "timestamp": "2026-10-24T12:00:00Z",
            "lint": {"command": "ruff check", "exit_code": 0, "output_tail": "All checks passed"},
            "tests": {"command": "python -m pytest -q", "exit_code": 0, "passed": 42, "failed": 0, "output_tail": "42 passed"},
            "secrets": {"command": "gitleaks detect --no-git", "exit_code": 0, "leaks_found": 0},
            "overall": "pass",
        }
        parsed = json.loads(json.dumps(example))
        self.assertEqual(parsed["gate"], "G2")
        self.assertTrue(parsed["story"])
        self.assertIn("T", parsed["timestamp"])
        datetime.fromisoformat(parsed["timestamp"].replace("Z", "+00:00"))
        self.assertTrue(REQUIRED_CHECKS.issubset(parsed))
        self.assertIn(parsed["overall"], VALID_STATUSES)
        for check in REQUIRED_CHECKS:
            self.assertEqual(parsed[check]["exit_code"], 0)

    def test_skipped_check_is_not_a_pass(self):
        skipped = {"skipped": True, "reason": "gitleaks executable is unavailable"}
        self.assertIs(skipped["skipped"], True)
        self.assertTrue(skipped["reason"].strip())
        self.assertNotIn("exit_code", skipped)


if __name__ == "__main__":
    unittest.main()

