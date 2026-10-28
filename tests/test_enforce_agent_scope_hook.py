"""Tests for the Claude Code write-scope hook."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "enforce_agent_scope_hook.py"
# Denials append telemetry; keep test events out of the team's real log.
TELEMETRY = Path(tempfile.mkdtemp()) / "activity.jsonl"


def invoke(payload):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "AI_TEAM_TELEMETRY_LOG": str(TELEMETRY)},
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
        telemetry = TELEMETRY
        real_log = ROOT / ".claude/telemetry/activity.jsonl"
        real_before = real_log.read_text(encoding="utf-8") if real_log.exists() else ""
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
        self.assertEqual(real_log.read_text(encoding="utf-8") if real_log.exists() else "", real_before)

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

    def bash_decision(self, command, cwd=str(ROOT), agent="agile-orchestrator"):
        payload = {"tool_name": "Bash", "cwd": cwd, "tool_input": {"command": command}}
        if agent:
            payload["agent_type"] = agent
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

    def test_coordinator_can_run_the_governance_scripts(self):
        commands = (
            "python scripts/detect_conflict.py --story US-12 --agents software-architect,tech-lead",
            "python scripts/check_approvals.py --story US-12 --checkpoint CP2",
            "python3 scripts/check_gates.py --story US-12 --gate G2",
            "python scripts/check_claims.py docs/project-state.md",
            "python scripts/enforce_agent_scope.py --agent backend-developer --path src/backend/app.py",
            "python scripts/coordinator_lock.py acquire --ttl 7200",
            "python scripts/coordinator_lock.py release",
            "python scripts/check_governance.py docs/sprints/*.md",
            "python scripts/check_governance.py --state docs/project-state.md --repo . --release",
            "python scripts/status_report.py --health-json --strict",
            "python scripts/add_lesson.py --title 'Pin actions' --context 'G2 lint' --error 'unpinned' --rule 'Pin SHAs' --story US-12",
            "./scripts/new_worktree.sh backend-developer US-12",
            "python3 scripts/provision_project.py plan .provisioning/shop-plan.json --check-github",
            "python3 scripts/provision_project.py apply .provisioning/shop-plan.json --dry-run",
            "python scripts/route_model.py --agent backend-developer --skill backend-engineering-standards --size M --risk",
            "python scripts/detect_checks.py",
            "python scripts/detect_checks.py --repo ../worktrees/wt-backend-developer-US-12",
            "python scripts/check_diff_scope.py --agent backend-developer",
            "python scripts/check_diff_scope.py --agent backend-developer --base main --repo ../worktrees/wt-backend-developer-US-12",
        )
        for agent in ("agile-orchestrator", None):  # None: the main session started without --agent
            for command in commands:
                with self.subTest(agent=agent, command=command):
                    self.assertEqual(self.bash_decision(command, agent=agent), "allow")

    def tool_decision(self, tool, tool_input, agent="backend-developer", cwd=str(ROOT)):
        payload = {"tool_name": tool, "cwd": cwd, "tool_input": tool_input}
        if agent:
            payload["agent_type"] = agent
        result = invoke(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] if result.stdout else "allow"

    def test_specialists_read_only_inside_the_repository_and_worktrees(self):
        worktree_file = str(ROOT.parent / "worktrees" / "wt-backend-developer-US-1" / "src" / "app.py")
        for tool, tool_input in (
            ("Read", {"file_path": str(ROOT / "README.md")}),
            ("Read", {"file_path": worktree_file}),
            ("Grep", {"pattern": "TODO", "path": str(ROOT / "scripts")}),
            ("Glob", {"pattern": "**/*.md"}),
        ):
            with self.subTest(tool=tool, tool_input=tool_input):
                self.assertEqual(self.tool_decision(tool, tool_input), "allow")
        for tool, tool_input in (
            ("Read", {"file_path": "/etc/passwd"}),
            ("Read", {"file_path": str(ROOT / ".." / ".." / "secret.txt")}),
            ("Read", {"file_path": "~/.ssh/id_rsa"}),
            ("Grep", {"pattern": "x", "path": "/home"}),
            ("Glob", {"pattern": "/etc/**"}),
            ("Glob", {"pattern": "../../**"}),
        ):
            with self.subTest(tool=tool, tool_input=tool_input):
                self.assertEqual(self.tool_decision(tool, tool_input), "deny")
        # The main session and the orchestrator are not restricted.
        self.assertEqual(self.tool_decision("Read", {"file_path": "/etc/hostname"}, agent=None), "allow")
        self.assertEqual(self.tool_decision("Read", {"file_path": "/etc/hostname"}, agent="agile-orchestrator"), "allow")

    def test_specialist_bash_reads_stay_inside_the_repository(self):
        for command in ("cat README.md", "grep -rn TODO scripts", "git log --oneline HEAD~3", "ls"):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command, agent="backend-developer"), "allow")
        for command in (
            "cat /etc/passwd",
            "cat ../../.ssh/id_rsa",
            "grep -r key /home",
            "grep -f/etc/shadow x",
            "grep --file=/etc/shadow x",
            "cat ~/.aws/credentials",
            "cat $HOME/.ssh/id_rsa",
            "head {/etc,x}/passwd",
            "ls ..",
            "git diff --no-index /etc/passwd README.md",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command, agent="backend-developer"), "deny")
        self.assertEqual(self.bash_decision("cat README.md", agent="backend-developer", cwd="/tmp"), "deny")
        self.assertEqual(self.bash_decision("cat /etc/hostname", agent=None), "allow")

    def test_writing_agents_write_in_their_own_worktree_only(self):
        worktrees = ROOT.parent / "worktrees"
        own = {"tool_name": "Write", "agent_type": "backend-developer", "tool_input": {"content": "x"}}
        for path, expected in (
            (worktrees / "wt-backend-developer-US-1" / "src" / "backend" / "app.py", "allow"),
            (worktrees / "wt-backend-developer-US-1" / "src" / "frontend" / "app.tsx", "deny"),
            (worktrees / "wt-frontend-developer-US-1" / "src" / "backend" / "app.py", "deny"),
            (Path("/tmp") / "src" / "backend" / "app.py", "deny"),
        ):
            with self.subTest(path=path):
                payload = {**own, "tool_input": {"file_path": str(path), "content": "x"}}
                result = invoke(payload)
                decision = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] if result.stdout else "allow"
                self.assertEqual(decision, expected)

    def test_ci_verifier_can_run_only_its_contract_checks(self):
        for command in (
            "python -m unittest discover -s tests",
            "python3 -m pytest -q tests",
            "ruff format --check scripts",
            "npm test",
            "make lint",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command, agent="ci-verifier"), "allow")
                self.assertEqual(self.bash_decision(command, agent="backend-developer"), "deny")
        for command in (
            "python -m unittest $(id)",
            "python -m pip install x",
            "python -m http.server",
            "npm install",
            "make deploy",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command, agent="ci-verifier"), "deny")

    def test_governance_scripts_are_limited_to_their_roles(self):
        self.assertEqual(
            self.bash_decision("python scripts/check_gates.py --story US-12 --gate G2", agent="backend-developer"), "deny"
        )
        self.assertEqual(
            self.bash_decision(
                "python scripts/add_lesson.py --title 'a' --context 'b' --error 'c' --rule 'd' --story US-1",
                agent="qa-automation",
            ),
            "deny",
        )
        self.assertEqual(self.bash_decision("./scripts/new_worktree.sh a US-1", agent="devops-platform"), "deny")
        self.assertEqual(
            self.bash_decision("python scripts/check_governance.py docs/sprints/S1.md", agent="project-manager"), "allow"
        )
        self.assertEqual(
            self.bash_decision("python scripts/check_governance.py docs/sprints/S1.md", agent="backend-developer"), "deny"
        )

    def test_governance_script_arguments_are_exact(self):
        for command in (
            "./scripts/cleanup_worktree.sh backend-developer US-12",
            "python scripts/coordinator_lock.py --lock-path /tmp/x status",
            "python scripts/check_gates.py --story US-12 --gate G3",
            "python scripts/check_claims.py ../outside.md",
            "python scripts/check_claims.py /etc/passwd",
            "python scripts/check_governance.py docs/*/*.md",
            "python scripts/add_lesson.py --title \"$HOME\" --context 'b' --error 'c' --rule 'd' --story US-1",
            "python scripts/add_lesson.py --title 'a' 'x' --context 'b' --error 'c' --rule 'd' --story US-1",
            "python scripts/detect_conflict.py --story US-12 --agents {a,b}",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_decision(command), "deny")
        relative = "python scripts/check_gates.py --story US-12 --gate G1"
        self.assertEqual(self.bash_decision(relative, cwd="/tmp"), "deny")

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
