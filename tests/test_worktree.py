"""Run the portable worktree shell regression suite from unittest discovery."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorktreeScriptTests(unittest.TestCase):
    def test_worktree_shell_suite(self) -> None:
        result = subprocess.run(
            ["bash", str(ROOT / "tests" / "test_worktree.sh")],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("All worktree tests passed.", result.stdout)
        self.assertGreaterEqual(result.stdout.count("PASS:"), 5, result.stdout)


if __name__ == "__main__":
    unittest.main()
