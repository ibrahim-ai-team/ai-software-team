"""Regression tests for fail-closed agent scope checks."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "enforce_agent_scope.py"
HOOK = ROOT / "scripts" / "enforce_agent_scope_hook.py"


def check(agent, path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--agent", agent, "--path", path], cwd=ROOT, capture_output=True, text=True, check=False
    )


class EnforceAgentScopeTests(unittest.TestCase):
    def test_backend_path_allowed(self):
        self.assertEqual(check("backend-developer", "src/backend/app.py").returncode, 0)

    def test_frontend_path_denied_to_backend(self):
        self.assertEqual(check("backend-developer", "src/frontend/app.tsx").returncode, 1)

    def test_absolute_path_denied(self):
        self.assertEqual(check("backend-developer", "/etc/passwd").returncode, 1)

    def test_unknown_agent_denied(self):
        self.assertEqual(check("agent-inconnu", "anything.txt").returncode, 1)

    def test_tech_lead_is_read_only(self):
        self.assertEqual(check("tech-lead", "README.md").returncode, 1)

    def test_empty_path_is_usage_error(self):
        self.assertEqual(check("backend-developer", "").returncode, 2)

    def test_recursive_glob_matches_nested_file(self):
        self.assertEqual(check("backend-developer", "src/backend/api/v1/handler.py").returncode, 0)

    def test_forbidden_overrides_allowlist(self):
        self.assertEqual(check("documentation-manager", ".claude/agents/backend-developer.md").returncode, 1)

    def test_frontend_and_backend_scopes_are_disjoint(self):
        self.assertEqual(check("frontend-developer", "src/backend/app.py").returncode, 1)
        self.assertEqual(check("backend-developer", "src/frontend/app.tsx").returncode, 1)

    def test_parent_traversal_denied(self):
        self.assertEqual(check("backend-developer", "src/backend/../../README.md").returncode, 1)

    def test_checker_does_not_modify_repository_files(self):
        before = {
            p.relative_to(ROOT).as_posix(): (p.stat().st_mtime_ns, p.stat().st_size)
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts
        }
        check("backend-developer", "src/backend/app.py")
        after = {
            p.relative_to(ROOT).as_posix(): (p.stat().st_mtime_ns, p.stat().st_size)
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts
        }
        self.assertEqual(before, after)

    def hook(self, command, agent="backend-developer"):
        payload = json.dumps(
            {
                "tool_name": "Bash",
                "agent_type": agent,
                "tool_input": {"command": command},
            }
        )
        return subprocess.run(
            [sys.executable, str(HOOK)],
            cwd=ROOT,
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_bash_write_redirect_is_blocked(self):
        result = self.hook('echo "x" > src/frontend/f.tsx')
        self.assertEqual(result.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', result.stdout)

    def test_bash_sed_inplace_is_blocked(self):
        result = self.hook("sed -i 's/a/b/' src/frontend/f.tsx")
        self.assertEqual(result.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', result.stdout)

    def test_bash_cp_to_forbidden_path_is_blocked(self):
        result = self.hook("cp a src/frontend/b")
        self.assertEqual(result.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', result.stdout)

    def test_bash_safe_command_is_allowed(self):
        result = self.hook("git status")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
