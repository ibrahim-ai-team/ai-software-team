"""Tests for the deterministic diff-scope checker (real temporary git repositories)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_diff_scope.py"


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def write(repo, relative, text="x\n"):
    path = Path(repo) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CheckDiffScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Scope Test")
        git(self.repo, "config", "user.email", "scope-test@example.invalid")
        write(self.repo, "src/backend/app.py")
        write(self.repo, "src/frontend/view.tsx")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "switch", "-q", "-c", "feat/US-1-backend-developer")

    def run_check(self, agent="backend-developer", *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--agent", agent, "--repo", str(self.repo), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_in_scope_changes_pass(self):
        write(self.repo, "src/backend/app.py", "changed\n")
        git(self.repo, "commit", "-qam", "edit")
        write(self.repo, "tests/backend/test_app.py")  # untracked, still in scope
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("IN_SCOPE src/backend/app.py", result.stdout)
        self.assertIn("IN_SCOPE tests/backend/test_app.py", result.stdout)

    def test_every_kind_of_out_of_scope_change_is_reported(self):
        write(self.repo, "src/frontend/view.tsx", "committed\n")
        git(self.repo, "commit", "-qam", "frontend edit")
        write(self.repo, ".claude/lessons/lessons.md")  # untracked governance file
        git(self.repo, "rm", "-q", "--cached", "src/backend/app.py")  # staged deletion stays in scope
        write(self.repo, "README.md", "unstaged\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for path in ("src/frontend/view.tsx", ".claude/lessons/lessons.md", "README.md"):
            self.assertIn(f"OUT_OF_SCOPE {path}", result.stdout)
        self.assertIn("IN_SCOPE src/backend/app.py", result.stdout)

    def test_no_changes_and_unknown_agent(self):
        self.assertEqual(self.run_check().returncode, 0)
        write(self.repo, "src/backend/app.py", "changed\n")
        self.assertEqual(self.run_check("not-an-agent").returncode, 1)

    def test_invalid_base_and_git_errors_exit_two(self):
        for base in ("--upload-pack=x", "main..other", "-x"):
            with self.subTest(base=base):
                self.assertEqual(self.run_check("backend-developer", f"--base={base}").returncode, 2)
        self.assertEqual(self.run_check("backend-developer", "--base", "no-such-branch").returncode, 2)


if __name__ == "__main__":
    unittest.main()
