---
description: Select and execute the next safe Ready story
---

# Next story

1. Reconcile project state, backlog, active delegations, current branch, and uncommitted changes before selecting work.
2. Select the highest-priority Ready story whose dependencies are complete and whose acceptance criteria are testable. If `tech-lead` has not split it into tasks yet, delegate that first.
3. If no story is Ready, report the exact blocker and propose the smallest action that unblocks work.
4. Assign a stable task ID, one accountable owner, explicit scope/allowed paths, dependencies, inputs, outputs, and evidence required. Choose the relevant skill from the routing table in `.claude/CLAUDE.md` and include the exact paths in the delegation record. Before accepting changes, compare `git diff --name-only` with allowed paths; reject or isolate out-of-scope edits. This is a coordinator check, not an OS-level write sandbox.
5. Implement only the bounded story. Avoid overlapping edits when sharing a working tree; parallel coding requires isolated worktrees and non-overlapping ownership.
6. Run relevant tests and security checks, inspect the diff, compare changed paths against the delegation allowlist, and report verified results. Never mark Done based on agent claims alone. For implementation, use `backend-developer`, `frontend-developer`, `database-engineer`, or `devops-platform` according to the approved task; use `qa-automation` for test work and validation, then `tech-lead` for the technical review and `code-review-security` for the read-only security review. Open the PR and leave it for the human merge.