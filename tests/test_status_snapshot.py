import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import status_snapshot  # noqa: E402

STATE = """# Project State
## Backlog and task ownership
| Task ID | Status | Priority | Owner | Dependencies | Acceptance/evidence |
|---|---|---|---|---|---|
| TASK-1 | Done | High | qa-automation | — | verified |
## Active delegations
| Delegation ID | Task ID | Owner | Branch/worktree | Scope/allowed paths | Expected output | Status | run_id | session_id | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| D1 | TASK-1 | qa-automation | feature/test | tests/ | result | In Progress | r1 | s1 | — |
"""

def write_event(path, stamp, details):
    path.write_text(
        json.dumps(
            {
                "ts": stamp.isoformat(),
                "agent_id": "qa-automation",
                "story": "TASK-1",
                "action": "tool_call",
                "details": details,
                "event_id": "e1",
            }
        )
        + "\n",
        encoding="utf-8",
    )

class SnapshotTests(unittest.TestCase):
    def setup_files(self, directory):
        state, log = Path(directory) / "project-state.md", Path(directory) / "activity.jsonl"
        state.write_text(STATE, encoding="utf-8")
        log.write_text("", encoding="utf-8")
        return state, log

    def test_no_events_unknown_without_drift(self):
        with tempfile.TemporaryDirectory() as d:
            state, log = self.setup_files(d)
            with patch.object(status_snapshot, "get_github", return_value=None):
                result = status_snapshot.build_snapshot(state, log, datetime.now(timezone.utc))
            agent = next(a for a in result["agents"] if a["agent_id"] == "qa-automation")
            self.assertEqual(agent["staleness"], "UNKNOWN")
            self.assertFalse(agent["drift"])

    def test_event_60_seconds_ago_is_fresh(self):
        with tempfile.TemporaryDirectory() as d:
            state, log = self.setup_files(d)
            now = datetime.now(timezone.utc)
            write_event(log, now - timedelta(seconds=60), {"status": "running"})
            with patch.object(status_snapshot, "get_github", return_value=None):
                result = status_snapshot.build_snapshot(state, log, now)
            agent = next(a for a in result["agents"] if a["agent_id"] == "qa-automation")
            self.assertEqual(agent["staleness"], "FRESH")

    def test_25_hour_event_unknown_but_reliable_drift_true(self):
        with tempfile.TemporaryDirectory() as d:
            state, log = self.setup_files(d)
            now = datetime.now(timezone.utc)
            write_event(log, now - timedelta(hours=25), {"status": "idle"})
            with patch.object(status_snapshot, "get_github", return_value=None):
                result = status_snapshot.build_snapshot(state, log, now)
            agent = next(a for a in result["agents"] if a["agent_id"] == "qa-automation")
            self.assertEqual(agent["staleness"], "UNKNOWN")
            self.assertTrue(agent["drift"])

    def test_open_issue_drifts_from_done(self):
        with tempfile.TemporaryDirectory() as d:
            state, log = self.setup_files(d)
            gh = {"issues": [{"number": 1, "title": "TASK-1 task", "body": "", "state": "OPEN"}], "pull_requests": []}
            with patch.object(status_snapshot, "get_github", return_value=gh):
                result = status_snapshot.build_snapshot(state, log, datetime.now(timezone.utc))
            task = next(t for t in result["tasks"] if t["task_id"] == "TASK-1")
            self.assertEqual(task["observed"], "IN_PROGRESS")
            self.assertTrue(task["drift"])

    def test_missing_gh_is_graceful(self):
        with patch.object(status_snapshot.shutil, "which", return_value=None):
            self.assertIsNone(status_snapshot.get_github())

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            state, log = self.setup_files(d)
            output = Path(d) / "snapshot.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/status_snapshot.py"),
                    "--state",
                    str(state),
                    "--activity",
                    str(log),
                    "--output",
                    str(output),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["schema_version"], 1)
            self.assertFalse(output.exists())

if __name__ == "__main__":
    unittest.main()
