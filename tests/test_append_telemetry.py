"""Regression tests for the telemetry append and analysis scripts."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from scripts import analyze_telemetry, append_telemetry


class AppendTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.log_path = Path(self.temp_dir.name) / "activity.jsonl"
        self.agents_path = Path(self.temp_dir.name) / "agents.json"
        self.agents_path.write_text(
            json.dumps({"agent_ids": ["agile-orchestrator", "qa-automation"]}),
            encoding="utf-8",
        )

    def run_append(self, details=None, extra_args=(), agent="agile-orchestrator", env=None):
        args = ["append_telemetry.py"]
        if agent is not None:
            args.extend(["--agent", agent])
        args.extend([
            "--action",
            "delegate",
            "--story",
            "US-1",
            "--details",
            details if details is not None else '{"target":"qa-automation"}',
            *extra_args,
        ])
        with (
            patch.object(sys, "argv", args),
            patch.object(append_telemetry, "LOG_PATH", self.log_path),
            patch.object(append_telemetry, "AGENTS_PATH", self.agents_path),
            patch.dict(os.environ, env or {}, clear=False),
        ):
            return append_telemetry.main()

    def read_events(self):
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
        ]

    def test_appends_iso_timestamp_and_uuid4(self):
        self.assertEqual(self.run_append(), 0)
        event = self.read_events()[0]
        datetime.fromisoformat(event["ts"])
        for field in ("trace_id", "session_id", "run_id", "event_id"):
            parsed_uuid = uuid.UUID(event[field])
            self.assertEqual(parsed_uuid.version, 4, field)
        self.assertEqual(event["agent"], "agile-orchestrator")
        self.assertEqual(event["agent_id"], "agile-orchestrator")
        self.assertEqual(event["action"], "delegate")
        self.assertTrue(all(event[field] for field in ("agent_id", "session_id", "run_id", "event_id")))

    def test_same_session_two_events_share_session_id_but_have_distinct_event_ids(self):
        session_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        options = ("--session-id", session_id, "--run-id", run_id)
        self.assertEqual(self.run_append(extra_args=options), 0)
        self.assertEqual(self.run_append(extra_args=options), 0)
        first, second = self.read_events()
        self.assertEqual(first["session_id"], second["session_id"])
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertNotEqual(first["event_id"], second["event_id"])

    def test_two_generated_sessions_have_distinct_session_ids(self):
        self.assertEqual(self.run_append(), 0)
        self.assertEqual(self.run_append(), 0)
        first, second = self.read_events()
        self.assertNotEqual(first["session_id"], second["session_id"])

    def test_unknown_agent_id_raises_clear_exception(self):
        with self.assertRaisesRegex(ValueError, "unknown agent_id"):
            append_telemetry.validate_agent_id("unknown-agent", self.agents_path)

    def test_agent_id_can_come_from_environment(self):
        self.assertEqual(self.run_append(agent=None, env={"AGENT_ID": "qa-automation"}), 0)
        event = self.read_events()[0]
        self.assertEqual(event["agent_id"], "qa-automation")
        self.assertEqual(event["agent"], "qa-automation")

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
        self.assertIn("Legacy events: 0", summary)
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
        self.assertIn("Legacy events: 3", summary)
        self.assertIn("Average duration: 20.00s", summary)

    def test_analyzer_counts_legacy_and_enriched_events_together(self):
        enriched = {
            "ts": "2026-01-01T00:00:00+00:00",
            "agent": "qa-automation",
            "action": "gate",
            "story": "US-2",
            "agent_id": "qa-automation",
            "session_id": str(uuid.uuid4()),
            "run_id": str(uuid.uuid4()),
            "event_id": str(uuid.uuid4()),
        }
        legacy = {
            "ts": "2026-01-01T00:00:05+00:00",
            "agent": "agile-orchestrator",
            "action": "delegate",
            "story": "US-2",
        }
        summary = analyze_telemetry.summarize([legacy, enriched])
        self.assertIn("Events: 2", summary)
        self.assertIn("Legacy events: 1", summary)
        self.assertIn("qa-automation=1", summary)
        self.assertIn("agile-orchestrator=1", summary)


if __name__ == "__main__":
    unittest.main()
