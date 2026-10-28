---
description: Select and execute the next safe Ready story
---

# Next story

1. Reconcile project state, backlog, active delegations, current branch, and uncommitted changes before selecting work.
2. Select the highest-priority Ready story whose dependencies are complete and whose acceptance criteria are testable. If `tech-lead` has not split it into tasks yet, delegate that first. Before marking a frontend task Ready or delegating it, apply `workflows/design-gate.md`: run `python scripts/check_governance.py --frontend-readiness --design-handoff <handoff-file>` and require exit code 0. With no handoff, the check fails closed; create one from `templates/design-handoff-template.md` and delegate design first. A missing or failed check blocks only frontend delegation; continue independent backend or analysis work where safe.
3. If no story is Ready, report the exact blocker and propose the smallest action that unblocks work.
4. Assign a stable task ID, one accountable owner, explicit scope/allowed paths, dependencies, inputs, outputs, and evidence required. Choose the relevant skill from the routing table in `.claude/agents/agile-orchestrator.md` and include the exact paths in the delegation record. Before accepting changes, run `python scripts/check_diff_scope.py --agent <agent> --repo ../worktrees/<worktree>`; any `OUT_OF_SCOPE` path (exit 1) means reject or isolate that edit, which is your decision. This is a coordinator check, not an OS-level write sandbox.
5. Implement only the bounded story. Avoid overlapping edits when sharing a working tree; parallel coding requires isolated worktrees and non-overlapping ownership.
6. Have `ci-verifier` run the applicable checks, inspect the diff, re-run `scripts/check_diff_scope.py` on the final branch, and report verified results. Never mark Done based on agent claims alone. For implementation, use `backend-developer`, `frontend-developer`, `database-engineer`, or `devops-platform` according to the approved task; use `qa-automation` for test work and validation, then `tech-lead` for the technical review and `code-review-security` for the read-only security review. Open the PR and leave it for the human merge.
