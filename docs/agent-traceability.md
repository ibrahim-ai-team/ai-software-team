# Agent Delegation and Project Traceability

## Purpose

Make project progress inspectable without requiring the sponsor to read every agent conversation. This is a recording protocol for the active Claude Code coordinator; it is not automatic telemetry and does not capture local subagent activity unless the coordinator records it.

## Sources of truth

Use the most authoritative available source for each fact:

- **Product definition:** approved product brief, requirements, acceptance criteria, assumptions/open questions.
- **Task state and priority:** GitHub Issues and configured GitHub Project; if unavailable, a project-local backlog/status file.
- **Implementation state:** current branch, commit, changed files, and linked PR.
- **Verification state:** exact test/build/lint commands, their observed results, and CI checks tied to the relevant commit.
- **Architecture:** ADRs and documented decisions.
- **Session continuity:** latest project-state summary and handover.
- **Agent activity:** delegation records written by the coordinator based on observed calls and returned results.

When sources disagree, do not silently choose the optimistic status. Record the mismatch, identify the latest verifiable source, and reconcile it.

## Stable delegation IDs

Give each delegated assignment a stable ID within the project, for example TASK-142-D01. Reuse that ID when updating the same assignment; create a new suffix for a genuinely new delegation. Include the ID in the issue comment, handover, or local activity record so that outputs can be traced.

A delegation record should include:

- linked issue/task and agent role;
- objective, context/inputs, expected output, acceptance checks;
- dependencies and exclusive file ownership;
- status and timestamps only when observed;
- reported outcome and exact artifacts changed;
- coordinator disposition (accepted, needs changes, partial, blocked, or rejected);
- evidence links (commit, PR, CI run, test output, document);
- blocker, next action, and owner when applicable.

Use templates/agent-delegation-template.md. Never record private chain-of-thought or unnecessary full transcripts.

## State model

Keep task, code, verification, and release states distinct.

- **Task:** `BACKLOG`, `READY`, `CLAIMED`, `IN_PROGRESS`, `BLOCKED`, `IN_REVIEW`, `CHANGES_REQUESTED`, `APPROVED_AWAITING_HUMAN_MERGE`, `DONE`, `CANCELLED` (same canonical vocabulary as `workflows/orchestration-contract.md`).
- **Claim validation:** `CONFIRMED` or `NEEDS_REVALIDATION`; this is a claim flag, not a task status.
- **Reconciliation observation:** `UNKNOWN` may describe unavailable status evidence but is not a task status.
- **Delegation:** queued, running, completed, partial, blocked, failed, cancelled, rejected (recorded as a delegation result, not a task status).
- **Implementation:** not started, local change, committed, PR open.
- **Verification:** not run, running, passed, failed, partially passed, unavailable.
- **Integration/release:** awaiting human merge, merged, deployment pending, deployed, deployment verified.

A delegation can be completed while its output is still unreviewed. A PR can be approved but not merged. A merged change is not necessarily deployed. Never collapse these states into one "done" label.

## Coordinator protocol

### Before delegation

1. Read the task, repo instructions, acceptance criteria, relevant decisions, and current state.
2. Confirm readiness, dependencies, and file ownership.
3. Create a unique delegation ID.
4. State inputs, output contract, acceptance checks, exact allowed paths, selected shared skill(s), and the reason they apply.
5. Record the delegation as queued/running in the issue or local activity log.

### After delegation

1. Record the actual returned result, not an imagined result.
2. Inspect the changed files/diff and evidence relevant to the acceptance criteria.
3. Decide whether to accept, request changes, mark partial, or escalate.
4. Link artifacts and update task/project status.
5. If the agent failed or did not return, record that accurately and choose a retry, alternative, or blocker. On a new coordinator session, mark unreconfirmed claims `NEEDS_REVALIDATION` and inspect their branch/worktree before resuming or reassigning.
6. Ensure only one implementation owner edits a given working tree at a time. Compare `git diff --name-only` against allowed paths before accepting output; treat this as coordinator verification, not a runtime sandbox.

### At session end

Reconcile every delegation from the session. No delegation may disappear from the report merely because its output was incomplete. Update the project-state summary and handover; list the next 1–3 actions.

## Meaningful activity events

Record material events only: delegation started/returned, output accepted/rejected, blocker opened/resolved, PR created/updated/reviewed, check started/completed, human decision requested/received, merge/deployment observed. Use templates/agent-activity-template.md as a compact shape.

Do not generate fake timestamps, fabricate tool calls, or claim that an agent worked between sessions. If the coordinator cannot observe an event, label it unknown/not verified.

## Daily report requirements

Use templates/daily-project-report-template.md. Include:

- report date/time and the evidence snapshot boundary;
- current product/sprint goal;
- verified completed items and links;
- in-progress/partial/blocked items with owner and next action;
- open PRs and whether they are awaiting review or human merge;
- verification results, exact commands/CI links, and checks not run;
- risks, material decisions needed, and next 1–3 priorities;
- explicit statement of what is not verified.

A daily report describes the last observed state. It does not imply continuous monitoring or background work while Claude Code is closed.

## Privacy, cost, and context discipline

Record concise summaries, identifiers, status, decisions, evidence, and next actions—not hidden reasoning or full transcripts. Avoid secrets and personal data in issue comments and activity records. Batch status updates where practical, use compact handovers, and stop unnecessary delegation when token/time budgets are tight.

## GitHub unavailable

If the repository/project integration is not configured or fails, do not claim remote tracking was updated. Keep a local project-state file and handover where possible, state that remote sync is pending, and reconcile it when GitHub access returns.

## Completion rule

A task is complete only when its acceptance criteria and required verification are satisfied, its evidence is recorded, and the relevant integration/review state is accurate. Under this team's policy, the user alone merges PRs; before merge, use **Approved — Awaiting Human Merge**, not Done.
