#!/usr/bin/env python3
"""Reject conflicting active claims in a project state file.

Reads the "Active delegations" table (see templates/project-state-template.md)
and fails when two active claims (CLAIMED / IN_PROGRESS) share a task, share a
branch/worktree, or have overlapping allowed paths. This is a pre-dispatch
check run by the single coordinator, not a distributed lock.

Usage: check_claims.py <project-state.md> [...]
"""
from pathlib import Path
import sys

ACTIVE = {"claimed", "in_progress", "in progress"}
REQUIRED = ("delegation id", "task id", "owner", "branch/worktree", "scope/allowed paths", "status")


def parse_rows(text: str) -> list[tuple[int, dict[str, str]]]:
    rows: list[tuple[int, dict[str, str]]] = []
    lines = text.splitlines()
    in_section = False
    header: list[str] = []
    for line_number, line in enumerate(lines, 1):
        if line.startswith("#"):
            in_section = line.lstrip("#").strip().lower() == "active delegations"
            header = []
            continue
        if not in_section or not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not header:
            header = [cell.lower() for cell in cells]
        elif not all(set(cell) <= set("-: ") for cell in cells):
            rows.append((line_number, dict(zip(header, cells))))
    return rows


def paths_overlap(left: str, right: str) -> bool:
    def norm(path: str) -> str:
        return path.strip().strip("`").rstrip("*").rstrip("/")
    a, b = norm(left), norm(right)
    return a == b or a == "" or b == "" or a.startswith(b + "/") or b.startswith(a + "/")


def check_claims(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rows = parse_rows(text)
    if rows and not set(REQUIRED) <= set(rows[0][1]):
        return [f"{path}: Active delegations table must have columns {', '.join(REQUIRED)}"]
    active = [(n, r) for n, r in rows if r.get("status", "").lower() in ACTIVE]
    errors: list[str] = []
    for index, (line_a, a) in enumerate(active):
        for line_b, b in active[index + 1:]:
            where = f"{path}:{line_b}: {b['delegation id']} conflicts with {a['delegation id']} (line {line_a})"
            if a["task id"] and a["task id"] == b["task id"]:
                errors.append(f"{where}: same task {a['task id']} claimed twice")
            if a["branch/worktree"] and a["branch/worktree"] == b["branch/worktree"]:
                errors.append(f"{where}: same branch/worktree {a['branch/worktree']}")
            for pa in a["scope/allowed paths"].split(","):
                for pb in b["scope/allowed paths"].split(","):
                    if paths_overlap(pa, pb):
                        errors.append(f"{where}: overlapping allowed paths {pa.strip()} / {pb.strip()}")
    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    failures = [error for arg in sys.argv[1:] for error in check_claims(Path(arg))]
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print("Claim check passed.")
