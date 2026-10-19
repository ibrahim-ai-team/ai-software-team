import tempfile
import unittest
from pathlib import Path

from scripts.check_claims import check_claims

HEADER = ("## Active delegations\n"
          "| Delegation ID | Task ID | Owner | Branch/worktree | Scope/allowed paths | Expected output | Status | Evidence |\n"
          "|---|---|---|---|---|---|---|---|\n")


def row(delegation, task, branch, paths, status="IN_PROGRESS"):
    return f"| {delegation} | {task} | agent | {branch} | {paths} | output | {status} | - |\n"


class ClaimTests(unittest.TestCase):
    def check(self, rows: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "project-state.md"
            path.write_text("# State\n" + HEADER + rows + "\n## Next\n| a | b |\n", encoding="utf-8")
            return check_claims(path)

    def test_disjoint_claims_pass(self):
        self.assertEqual(self.check(row("D01", "S-1", "feat/s1", "src/api/") + row("D02", "S-2", "feat/s2", "src/web/")), [])

    def test_same_task_is_rejected(self):
        errors = self.check(row("D01", "S-1", "feat/a", "src/a/") + row("D02", "S-1", "feat/b", "src/b/"))
        self.assertTrue(any("same task S-1" in e for e in errors), errors)

    def test_same_branch_is_rejected(self):
        errors = self.check(row("D01", "S-1", "feat/x", "src/a/") + row("D02", "S-2", "feat/x", "src/b/"))
        self.assertTrue(any("same branch/worktree feat/x" in e for e in errors), errors)

    def test_overlapping_paths_are_rejected_with_line(self):
        errors = self.check(row("D01", "S-1", "feat/a", "src/api/") + row("D02", "S-2", "feat/b", "src/api/users.py, docs/"))
        self.assertTrue(any("overlapping allowed paths" in e and "project-state.md:6" in e for e in errors), errors)

    def test_released_claims_do_not_conflict(self):
        self.assertEqual(self.check(row("D01", "S-1", "feat/a", "src/", "DONE") + row("D02", "S-1", "feat/a", "src/")), [])

    def test_missing_columns_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.md"
            path.write_text("## Active delegations\n| Delegation ID | Owner | Status |\n|---|---|---|\n| D01 | a | CLAIMED |\n", encoding="utf-8")
            self.assertTrue(any("must have columns" in e for e in check_claims(path)))


if __name__ == "__main__":
    unittest.main()
