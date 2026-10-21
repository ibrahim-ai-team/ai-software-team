# GitHub Projects status transition policy

## Source of truth

The GitHub Project's single-select Status field is the canonical board status. Issue titles are for concise identification only; never parse or modify a title to infer or set the board status. The issue body may describe workflow intent, but it is not proof that the board was updated.

Use these status options when configuring the Project:

- Backlog
- Ready
- In Progress
- In Review
- Changes Requested
- Approved — Awaiting Human Merge
- Blocked
- Done

If the existing board uses different exact labels, document an explicit mapping before enabling automation. Do not silently create a second competing Status field.

## Allowed transitions and evidence

| From | To | Trigger | Required evidence |
| --- | --- | --- | --- |
| Backlog | Ready | PM accepts Definition of Ready | Completed readiness checklist; acceptance criteria; QA mapping; dependencies/estimate |
| Ready | In Progress | Coordinator assigns one owner and work starts | Owner, branch/worktree and start checkpoint |
| In Progress | In Review | PR opened and implementation is ready for review | PR URL, linked issue, changed files, checks run and results |
| In Review | Changes Requested | Review finds actionable issues | Review findings linked to files/lines and required fixes |
| Changes Requested | In Progress | Owner begins requested corrections | Findings acknowledged and correction work started |
| Changes Requested | In Review | New revision submitted | New commit/revision and re-run checks |
| In Review | Approved — Awaiting Human Merge | Coordinator verifies current revision is acceptable | Review disposition, required CI status, acceptance/test evidence; unrun checks disclosed |
| Approved — Awaiting Human Merge | Done | Human merges and completion is reconciled | Merged PR URL/commit, required checks, acceptance criteria verified |
| Any non-terminal status | Blocked | A dependency, access, environment or decision prevents safe progress | Blocker, impact, attempted resolution, needed owner/decision and next action |
| Blocked | Backlog | Scope/dependency changed; task needs replanning | Updated dependency and reason |
| Blocked | Ready | Blocker resolved and Definition of Ready still passes | Resolution evidence and readiness re-check |
| Done | In Progress | A regression/reopen is explicitly approved | Reopen reason, linked regression/bug and owner |
| (unset) | Backlog, Ready or Blocked | Item was added to the board without a Status | Triage reason; Ready also needs the Definition of Ready evidence |

A task cannot transition directly to Done just because a developer or subagent says done, a PR was opened/approved, or a test plan exists. Only a verified human merge and completion check permit Done under this policy. If the repository chooses a different Definition of Done, record it explicitly.

## Manual/automated update contract

1. The coordinator observes a real event and gathers the required evidence.
2. The coordinator invokes the explicit status-update workflow with issue number, target status, concise reason, and an evidence URL (PR, CI run, test report, or blocker record).
3. The workflow validates the transition and required evidence, locates the exact issue in the configured Project V2, finds the actual Status field/option IDs, and updates that field.
4. The workflow reads the field back and fails unless the returned value equals the requested status.
5. The coordinator reports the result only after the read-back confirms it. If token permissions, project membership, pagination, field name or option mismatch prevents confirmation, keep the last verified status and report the failure.
6. Never claim that issue state, labels, title text, or an issue-body prefix alone changed the board field.
7. Do not automatically set Done based only on PR close events; verify merged state and required evidence. Do not merge PRs automatically; the human owner retains merge authority.

## Project configuration

The current repository documentation describes manual setup and does not create boards. Board creation/configuration is a separate authorized bootstrap operation. Before creating a new Project, check whether the intended project already exists, confirm owner/org, project number, field names/options, visibility and permissions. Do not create duplicate boards or change organization permissions implicitly.
