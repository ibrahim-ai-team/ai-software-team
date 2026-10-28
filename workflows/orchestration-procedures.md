# Orchestration procedures

Detailed procedures behind `workflows/orchestration-contract.md`. The contract states each rule and links here; read a section only when you are doing that step.

## Contents

| Section | Read when |
| --- | --- |
| [Local single-coordinator lock](#local-single-coordinator-lock) | Starting or ending a session |
| [Claim protocol](#claim-protocol) | Dispatching, releasing or recovering a delegation |
| [Execution identity and telemetry correlation](#execution-identity-and-telemetry-correlation) | Recording telemetry or an Active delegations row |
| [Threat-model checkpoint](#threat-model-checkpoint) | In `ARCHITECTURE`, before implementation |
| [Continuous learning after failed Gates](#continuous-learning-after-failed-gates) | A G1 or G2 check failed |
| [Backlog and project status integrity](#backlog-and-project-status-integrity) | Creating issues or changing board status |
| [Acceptance checklist for a usable orchestration run](#acceptance-checklist-for-a-usable-orchestration-run) | Before ending a session |

## Local single-coordinator lock

Before reconciliation or delegation, run `python scripts/coordinator_lock.py acquire`. If it exits `2`, stop and inspect `python scripts/coordinator_lock.py status`; never coordinate concurrently while a non-expired lock is held. The default TTL is 3,600 seconds (raise with `--ttl` for longer sessions; an expired lock can be taken over with a warning). After the handover and Project Manager report, run `python scripts/coordinator_lock.py release`. Release refuses a live lock held by another host or user. The lock at `state/coordinator.lock` is a **same-machine local lock only**, not a distributed lock service.

## Claim protocol

Single coordinator, no lock service:

1. *Claim:* add a row to the project state's Active delegations table (delegation ID, task ID, owner, branch/worktree, allowed paths, status `CLAIMED`), run `python scripts/check_claims.py <state file>`, and dispatch only if it passes; then set `IN_PROGRESS`.
2. *Release:* when the agent returns, verify the branch/PR evidence, then set `IN_REVIEW`, `BLOCKED`, `DONE` or `CANCELLED`. Only `CLAIMED`/`IN_PROGRESS` rows hold paths.
3. *Recover:* at the next session, mark unconfirmed active rows `NEEDS_REVALIDATION`, inspect their branch/worktree, then resume, release to `BLOCKED` with partial work preserved, or reassign after release. Never reassign a row that is still active.
4. *Conflict:* if two writers touched the same branch or paths, stop both, keep each result on its own branch, and reconcile in one follow-up task.

Claims record `claimed-at`, last observed checkpoint, owner, branch/worktree and allowed paths. Do not promise heartbeat or timeout behavior unless a real mechanism exists, and never auto-steal a claim because time elapsed.

## Execution identity and telemetry correlation

Each telemetry event keeps the existing fields and adds `agent_id`, `session_id`, `run_id` and a unique UUID4 `event_id`. Resolve `agent_id` from `--agent-id`/`AGENT_ID` (or the backward-compatible `--agent`) and validate it against `state/agents.json`. Set `SESSION_ID` and `RUN_ID`, or pass `--session-id` and `--run-id`, when events share a session or run; otherwise the writer generates a fresh UUID4 per invocation. Never rename or remove `agent` or `trace_id`. Record `run_id` and `session_id` in every Active delegations row. Historical events without these fields remain readable and count as legacy in `scripts/analyze_telemetry.py`.

## Threat-model checkpoint

During `ARCHITECTURE`, before implementation, require a documented threat model whenever the system handles authentication/authorization, personal or sensitive data, external integrations/webhooks, file uploads, payments, secrets or privileged operations. Use `.claude/skills/security-threat-modelling/SKILL.md` and record assets, trust boundaries, abuse cases, mitigations, residual risks and verification tasks. With no meaningful security-sensitive flow, record `NOT APPLICABLE` with a short rationale.

## Continuous learning after failed Gates

At every failed Gate (G1 or G2), preserve the failing check and safe evidence, then **call `scripts/add_lesson.py` before retrying** with the sanitized context, observed error, rule to apply and originating story ID. Never copy logs or payloads that may contain credentials, tokens, passwords or secrets into a lesson; the writer rejects suspicious terms and credential-like values, but the caller remains responsible for redaction. Then reread `.claude/lessons/lessons.md`, include relevant lessons in the retry brief, and change the remediation strategy. If a lesson cannot be safely recorded, stop and report the blocker.

## Backlog and project status integrity

Follow `workflows/sprint-governance.md` for sprint planning, scope changes, closure and release criteria, and the issue creation gate in `workflows/backlog-quality-gates.md` before creating any issue or calling a task Ready. QA maps acceptance criteria to verification methods and identifies distinct linked QA issues before sprint commitment. Follow `workflows/project-status-transitions.md` for the Project Status field and allowed transitions. A title prefix, body text, label or agent assertion does not prove a board status changed: verify the actual Project V2 field after each update, report failures without claiming success, and keep the last verified state. Never set Done without a verified human-merged PR and completion evidence.

## Acceptance checklist for a usable orchestration run

- [ ] State reconciled against current repository, issues, PRs and CI.
- [ ] Phase and next task are explicit.
- [ ] Every active task has unique ID, owner, dependencies, allowed paths and acceptance checks.
- [ ] No overlapping writer in a shared working tree.
- [ ] Delegation outcomes are independently reconciled.
- [ ] Actual checks and evidence are linked.
- [ ] PRs await human merge.
- [ ] Daily report distinguishes implementation, testing, merge and deployment.
- [ ] Handover persists next action and blockers.
