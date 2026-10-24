"""Tests for the Claude Code write-scope hook."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "enforce_agent_scope_hook.py"


def invoke(payload):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ScopeHookTests(unittest.TestCase):
    def test_allowed_write_is_permitted(self):
        result = invoke(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "agent_type": "backend-developer",
                "tool_input": {
                    "file_path": str(ROOT / "src/backend/new.py"),
                    "content": "x",
                },
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_out_of_scope_write_is_blocked_and_telemetry_recorded(self):
        telemetry = ROOT / ".claude/telemetry/activity.jsonl"
        before = telemetry.read_text(encoding="utf-8") if telemetry.exists() else ""
        result = invoke(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "agent_type": "backend-developer",
                "tool_input": {
                    "file_path": str(ROOT / "src/frontend/blocked.tsx"),
                    "content": "secret-not-logged",
                },
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
        after = telemetry.read_text(encoding="utf-8")
        self.assertGreater(len(after), len(before))
        event = json.loads(after.splitlines()[-1])
        self.assertEqual(event["details"]["refused_path"], "src/frontend/blocked.tsx")
        self.assertNotIn("secret-not-logged", after)

    def test_unknown_subagent_fails_closed(self):
        result = invoke(
            {
                "tool_name": "Edit",
                "agent_type": "not-configured",
                "tool_input": {"file_path": str(ROOT / "README.md")},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )

    def test_main_session_write_is_not_scoped_by_agent_policy(self):
        result = invoke(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(ROOT / "README.md")},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_non_write_tool_is_ignored(self):
        result = invoke(
            {
                "tool_name": "Read",
                "agent_type": "backend-developer",
                "tool_input": {"file_path": str(ROOT / "src/frontend/app.tsx")},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
