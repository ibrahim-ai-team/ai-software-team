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

    def bash_decision(self, command, cwd=str(ROOT)):
        payload = {"tool_name": "Bash", "agent_type": "agile-orchestrator", "cwd": cwd, "tool_input": {"command": command}}
        result = invoke(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] if result.stdout else "allow"

    def test_lessons_lookup_is_allowed(self):
        for command in (
            "python scripts/relevant_lessons.py --story SHOP-12 --max 5",
            "python3 scripts/relevant_lessons.py --story SMOKE-MODEL-05",
            f"python3 {ROOT / 'scripts/relevant_lessons.py'} --story S1 --max 3",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command), "allow")

    def test_other_python_commands_stay_denied(self):
        for command in (
            "python3 -c print(1)",
            "python3 scripts/add_lesson.py --story S1",
            "python3 scripts/relevant_lessons.py",
            "python3 scripts/relevant_lessons.py --story S1 --max 5 --extra x",
            "python3 scripts/relevant_lessons.py --story ../x --max 5",
            "python3 scripts/relevant_lessons.py --story S1 --max -1",
            "python3 scripts/relevant_lessons.py --story S1 > out.txt",
            "python3 -m scripts.relevant_lessons --story S1",
            "./python3 scripts/relevant_lessons.py --story S1",
            "/tmp/x/python3 scripts/relevant_lessons.py --story S1",
            # Shell expansion: bash would run something other than what shlex shows the hook.
            "python3 {-c,x}/../scripts/relevant_lessons.py --story S1",
            "python3 */../scripts/relevant_lessons.py --story S1",
            "python3 ~/../scripts/relevant_lessons.py --story S1",
            "python3 scripts/relevant_lessons.py --story S$IFS-c",
            "python3 scripts/./relevant_lessons.py --story S1",
            "python3  scripts/relevant_lessons.py --story S1",
            "python3 scripts/relevant_lessons.py --story S1 --max ²",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command), "deny")

    def test_read_only_commands_stay_allowed(self):
        for command in (
            "git status",
            "git diff --stat",
            "git log --oneline -3",
            "ruff check scripts",
            "find . -name x",
            "ls -la",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command), "allow")

    def test_path_qualified_commands_and_write_options_are_denied(self):
        for command in (
            "/tmp/x/git status",
            "./ls",
            "/usr/bin/cat README.md",
            "git diff --output=out.txt",
            "git log --output out.txt",
            "git diff --ext-diff",
            "git log -p --textconv",
            "ruff check --fix scripts",
            "ruff check --fix-only scripts",
            "ruff check --output-file=out.txt scripts",
            "ruff check -oout.txt scripts",
            "gitleaks detect --report-path=out.json",
            "gitleaks detect -r out.json",
            "find . -fprint out.txt",
            "find . -fprintf out.txt %p",
            "find . -fls out.txt",
            "find . -ok rm {}",
            "find . -okdir rm {}",
            "find . -exec rm {}",
            "find . -delete",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command), "deny")

    def test_relative_lessons_lookup_requires_repository_cwd(self):
        command = "python3 scripts/relevant_lessons.py --story S1"
        self.assertEqual(self.bash_decision(command, cwd="/tmp"), "deny")
        self.assertEqual(self.bash_decision(command, cwd=None), "deny")
        absolute = f"python3 {ROOT / 'scripts/relevant_lessons.py'} --story S1"
        self.assertEqual(self.bash_decision(absolute, cwd="/tmp"), "allow")

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
