"""Regression tests for the telemetry append and analysis scripts."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import analyze_telemetry, append_telemetry


class AppendTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.log_path = Path(self.temp_dir.name) / "activity.jsonl"
        self.argv = patch.object(
            sys,
            "argv",
            [
                "append_telemetry.py",
                "--agent",
                "agile-orchestrator",
                "--action",
                "delegate",
                "--story",
                "US-1",
                "--details",
                '{"target":"qa-automation"}',
            ],
        )
        self.argv.start()
        self.addCleanup(self.argv.stop)

    def run_append(self, details=None):
        args = [
            "append_telemetry.py", "--agent", "agile-orchestrator",
            "--action", "delegate", "--story", "US-1",
            "--details", details if details is not None else '{"target":"qa-automation"}',
        ]
        with patch.object(sys, "argv", args), patch.object(append_telemetry, "LOG_PATH", self.log_path):
            return append_telemetry.main()

    def test_appends_iso_timestamp_and_uuid4(self):
        self.assertEqual(self.run_append(), 0)
        event = json.loads(self.log_path.read_text(encoding="utf-8").strip())
        datetime.fromisoformat(event["ts"])
        parsed_uuid = uuid.UUID(event["trace_id"])
        self.assertEqual(parsed_uuid.version, 4)
        self.assertEqual(event["agent"], "agile-orchestrator")
        self.assertEqual(event["action"], "delegate")

    def test_rejects_invalid_json_without_appending(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_append("{invalid"), 1)
        self.assertFalse(self.log_path.exists())

    def test_rejects_sensitive_top_level_key(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_append('{"api_key":"dont-log"}'), 1)
        self.assertFalse(self.log_path.exists())

    def test_rejects_sensitive_nested_key(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_append('{"metadata":{"access_token":"dont-log"}}'), 1)
        self.assertFalse(self.log_path.exists())

    def test_append_is_append_only(self):
        self.assertEqual(self.run_append(), 0)
        first = self.log_path.read_text(encoding="utf-8")
        self.assertEqual(self.run_append('{"target":"backend-developer"}'), 0)
        contents = self.log_path.read_text(encoding="utf-8")
        self.assertTrue(contents.startswith(first))
        self.assertEqual(len(contents.splitlines()), 2)

    def test_analyzer_handles_empty_or_missing_file(self):
        empty = self.log_path
        empty.write_text("", encoding="utf-8")
        self.assertEqual(analyze_telemetry.load_events(empty), [])
        missing = empty.with_name("missing.jsonl")
        self.assertEqual(analyze_telemetry.load_events(missing), [])
        summary = analyze_telemetry.summarize([])
        self.assertIn("Events: 0", summary)
        self.assertEqual(len(summary.splitlines()), 3)

    def test_analyzer_summary_for_three_events(self):
        events = [
            {"ts": "2026-01-01T00:00:00+00:00", "agent": "agile-orchestrator", "action": "delegate", "story": "US-1"},
            {"ts": "2026-01-01T00:00:10+00:00", "agent": "qa-automation", "action": "gate", "story": "US-1"},
            {"ts": "2026-01-01T00:00:20+00:00", "agent": "qa-automation", "action": "error", "story": "US-1"},
        ]
        summary = analyze_telemetry.summarize(events)
        self.assertEqual(len(summary.splitlines()), 3)
        self.assertIn("Events: 3", summary)
        self.assertIn("agile-orchestrator=1", summary)
        self.assertIn("qa-automation=2", summary)
        self.assertIn("Errors: 1", summary)
        self.assertIn("Gates recorded: 1", summary)
        self.assertIn("Average duration: 20.00s", summary)


if __name__ == "__main__":
    unittest.main()
