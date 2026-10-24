"""Tests for local sprint ROI report generation."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.roi_report as roi_report


class RoiReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.metrics_path = Path(self.temp_dir.name) / "sprint-7.json"
        self.metrics_dir_patch = patch.object(roi_report, "METRICS_DIR", Path(self.temp_dir.name))
        self.metrics_dir_patch.start()
        self.addCleanup(self.metrics_dir_patch.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def write_json(self, data: object) -> None:
        self.metrics_path.write_text(json.dumps(data), encoding="utf-8")

    def test_three_stories_have_correct_rows_and_roi(self) -> None:
        self.write_json(
            {
                "stories": [
                    {"story_id": "US-1", "agent_minutes": 10, "tokens": 100000, "human_hours_estimated": 1},
                    {"story_id": "US-2", "agent_minutes": 20, "tokens": 200000, "human_hours_estimated": 2},
                    {"story_id": "US-3", "agent_minutes": 30, "tokens": 50000, "human_hours_estimated": 0.5},
                ]
            }
        )
        stories = roi_report.load_stories(self.metrics_path)
        report = roi_report.build_report(7, stories, 80, 0.000003)
        self.assertEqual(report.count("| US-"), 3)
        self.assertIn("| US-1 | 10 | 100000 | 0.300000 | 1 | 80.00 | 266.67 |", report)
        self.assertIn("| US-2 | 20 | 200000 | 0.600000 | 2 | 160.00 | 266.67 |", report)
        self.assertIn("| US-3 | 30 | 50000 | 0.150000 | 0.5 | 40.00 | 266.67 |", report)

    def test_empty_stories_reports_aucune_story(self) -> None:
        self.write_json({"stories": []})
        report = roi_report.build_report(7, roi_report.load_stories(self.metrics_path), 80, 0.000003)
        self.assertIn("Aucune story", report)

    def test_invalid_json_returns_clear_error_and_code_one(self) -> None:
        self.metrics_path.write_text("{invalid", encoding="utf-8")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = roi_report.main(["--sprint", "7"])
        self.assertEqual(code, 1)
        self.assertIn("Error: cannot read valid JSON", stderr.getvalue())

    def test_missing_required_argument_exits_two(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            roi_report.parse_args([])
        self.assertEqual(raised.exception.code, 2)

    def test_missing_story_fields_are_rejected(self) -> None:
        self.write_json({"stories": [{"story_id": "US-1", "tokens": 2}]})
        with self.assertRaises(roi_report.MetricsError):
            roi_report.load_stories(self.metrics_path)

    def test_zero_token_cost_has_defined_ratio(self) -> None:
        story = [{"story_id": "US-0", "agent_minutes": 1, "tokens": 0, "human_hours_estimated": 1}]
        self.assertIn(
            "| US-0 | 1 | 0 | 0.000000 | 1 | 80.00 | ∞ |",
            roi_report.build_report(7, story, 80, 0.000003),
        )


if __name__ == "__main__":
    unittest.main()
