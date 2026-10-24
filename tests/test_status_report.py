"""Tests for the human/programmatic status report."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "status_report.py"


def run_report(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class StatusReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.snapshot_path = Path(self.temp_dir.name) / "effective.json"
        self.snapshot = {
            "schema_version": 1,
            "generated_at": "2026-10-24T08:00:00Z",
            "agents": [
                {
                    "agent_id": f"agent-{index:02d}",
                    "declared": "running",
                    "observed": "running",
                    "drift": False,
                    "last_event_age_seconds": 30 + index,
                    "staleness": "FRESH",
                }
                for index in range(20)
            ],
            "tasks": [
                {
                    "task_id": "TASK-1",
                    "declared": "READY",
                    "observed": "IN_PROGRESS",
                    "drift": True,
                    "evidence": [],
                },
                {
                    "task_id": "TASK-2",
                    "declared": "DONE",
                    "observed": "DONE",
                    "drift": False,
                    "evidence": [],
                },
            ],
            "github": {"available": True, "issues_count": 2, "pull_requests_count": 1},
        }
        self.write_snapshot()

    def write_snapshot(self) -> None:
        self.snapshot_path.write_text(json.dumps(self.snapshot), encoding="utf-8")

    def with_snapshot(self, *args: str) -> subprocess.CompletedProcess[str]:
        return run_report("--snapshot", str(self.snapshot_path), *args)

    def test_json_mode_outputs_original_valid_snapshot(self):
        result = self.with_snapshot("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.snapshot)

    def test_agent_filter_keeps_only_requested_agent(self):
        result = self.with_snapshot("--json", "--filter", "agent=AGENT-07")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([agent["agent_id"] for agent in payload["agents"]], ["agent-07"])
        self.assertEqual(len(payload["tasks"]), 2)

    def test_task_filter_keeps_only_requested_task(self):
        result = self.with_snapshot("--json", "--filter", "task=TASK-2")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([task["task_id"] for task in payload["tasks"]], ["TASK-2"])
        self.assertEqual(len(payload["agents"]), 20)

    def test_missing_snapshot_warns_and_returns_valid_empty_json(self):
        missing = str(Path(self.temp_dir.name) / "missing.json")
        result = run_report("--snapshot", missing, "--json")
        self.assertEqual(result.returncode, 0)
        self.assertIn("WARNING: effective status snapshot not found", result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["agents"], [])
        self.assertEqual(payload["tasks"], [])

    def test_stale_snapshot_age_is_visible(self):
        self.snapshot["generated_at"] = "2000-01-01T00:00:00Z"
        self.write_snapshot()
        result = self.with_snapshot()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"STALE SNAPSHOT \(age: \d+s\)")
        self.assertRegex(result.stderr, r"STALE SNAPSHOT \(age: \d+s\)")

    def test_human_table_is_under_120_columns_for_20_agents(self):
        result = self.with_snapshot()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("last_event_age", result.stdout)
        for line in result.stdout.splitlines():
            self.assertLessEqual(len(line), 120, line)

    def test_filter_validation_fails_clearly(self):
        result = self.with_snapshot("--filter", "project=anything")
        self.assertEqual(result.returncode, 2)
        self.assertIn("filter must be agent=X or task=Y", result.stderr)


if __name__ == "__main__":
    unittest.main()
