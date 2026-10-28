# Orchestration Contract

## Purpose and limits

This contract defines the repeatable control loop for a Claude Code session. It is a protocol, not a background service, distributed lock manager, or proof that Claude Code can discover or delegate to every profile. The coordinator of record is `agile-orchestrator`, started as the main session with `claude --agent agile-orchestrator`; a session started without it follows the same contract. Delegation is hub-and-spoke: only the orchestrator has the `Agent` tool, and specialists return results to it and never call each other. Work stops when the session stops unless an independently configured scheduler invokes it.

## Canonical state

Keep a durable project state file in the project repository (recommended: `docs/project-state.md`) and task records in GitHub Issues when available. Keep sensitive values out of state files. Facts about code and checks come from the repository, commits, PR state and CI results; chat history and agent claims are context only, never proof. Task state comes from the canonical issue/Project status, then delegation records.

Every snapshot includes: project ID/name, last reconciled timestamp (UTC), current phase, product goal and approved MVP scope, release criteria and open requirement conflicts, current sprint record, approved decisions and ADR links, assumptions, task IDs/status/owner/dependencies, active delegation IDs, PRs, CI/test evidence, blockers, sponsor decisions needed, next actions, and last known commit. If GitHub is unavailable, use a local state file and say that remote sync is unavailable.

## Authority and precedence

When decisions, requirements or plans disagree, the higher source wins:

1. Security constraints and repository protections (`standards/security-principles.md`, `.claude/settings.json`, rulesets).
2. The latest explicit human (sponsor) decision, recorded with an ID and date in the project state.
3. Approved product scope and release criteria (`## Release criteria` in the project state).
4. The approved sprint goal and commitment (the sprint record, `workflows/sprint-governance.md`).
5. Accepted requirements and acceptance criteria (story issues and planning documents).
6. Repository standards and technical decisions (ADRs, `standards/`).
7. Agent suggestions and generated plans.

Rules:

- A lower source never silently overrides a higher one. An agent suggestion, an older requirement or a code constant does not override an approved human decision.
- On a conflict, the coordinator records it (project state `## Requirement conflicts`: criterion, sources, impact, decision needed), stops dependent work, and asks the decision owner (`standards/agent-contract.md#decision-authority`). It never picks the more ambitious or more convenient option itself.
- A newer decision supersedes an older one only for what it states. Record which requirement it replaces, then update every mirror.
- Each rule has one home: sprint rules in `workflows/sprint-governance.md`, issue creation in `workflows/backlog-quality-gates.md`, roles and decision authority in `standards/agent-contract.md`, status transitions in `workflows/project-status-transitions.md`. Commands and agent files link to them instead of copying them.

## Conflict Resolution

Follow [`standards/conflict-resolution.md`](../standards/conflict-resolution.md) for precedence, the two-strike escalation rule and the disagreement-record format. Before **every transition**, run:

```bash
python scripts/detect_conflict.py --story <story> --agents <agent-a,agent-b>
```

Exit `0` passes. Exit `1` (unresolved disagreement) means STOP and escalate to the human sponsor at the applicable CP1–CP4 checkpoint. Exit `2` (invalid input, unreadable record or malformed JSON) also means STOP. Never continue a dependent transition while a disagreement is unresolved; no agent may ignore or override an escalated conflict. The detector is read-only.

## HITL Enforcement

Human checkpoints are mandatory and distinct from automated Gates: a Gate records technical verification, only the human sponsor or a repository-authorized human approves a CP, and a passing Gate never satisfies a CP. Follow `standards/human-in-the-loop.md` for CP1 plan, CP2 architecture, CP3 code-before-merge and CP4 release-before-tag. Before every transition crossing a checkpoint, and before delegating implementation, run:

```bash
python scripts/check_approvals.py --story <story> --checkpoint CP<N>
```

Exit `0` is required to proceed. Exit `1` (record absent or invalid): stop and ask the human. Exit `2` (invalid invocation): fix the arguments and re-check. Never create approval records for the sponsor or infer approval from agent output, comments or a passing Gate. The checker is read-only and validates the record's fields and SHA-256 digest format; see the standard for its limits.

## Threat-model checkpoint

During `ARCHITECTURE`, before implementation, require a documented threat model whenever the system handles authentication/authorization, personal or sensitive data, external integrations/webhooks, file uploads, payments, secrets or privileged operations. Use `.claude/skills/security-threat-modelling/SKILL.md` and record assets, trust boundaries, abuse cases, mitigations, residual risks and verification tasks. With no meaningful security-sensitive flow, record `NOT APPLICABLE` with a short rationale.

## State machine

Project phases:

- `DISCOVERY`: capture idea, goals, users, outcomes, constraints.
- `SPECIFICATION`: PO/BA produce requirements, journeys, edge cases, acceptance criteria, NFRs, assumptions and open questions.
- `ARCHITECTURE`: Architect compares options and records the recommended architecture and trade-offs; Tech Lead validates buildability and sets implementation standards.
- `BACKLOG_READY`: PM (Scrum Master) builds the prioritized backlog and a two-week sprint (default length); Tech Lead splits stories into small, path-bounded tasks; QA/DevOps add verification and delivery needs.
- `AWAITING_SPONSOR_DECISION`: pause only for material business direction, spending, access/visibility, security-risk acceptance, destructive actions, production release or other irreversible commitment.
- `DELIVERY`: execute bounded Ready tasks.
- `INTEGRATION_REVIEW`: integrate outputs, run checks, QA and security review.
- `AWAITING_HUMAN_MERGE`: PR ready with evidence and reviews recorded; the human owner merges.
- `MAINTENANCE`: resume from reconciled state, repair blockers, continue the next priority.
- `BLOCKED`: no safe task can progress; report the exact blocker and requested action.
- `COMPLETE`: only when stated scope and Definition of Done are verified, not because a session ended.

Record each transition with timestamp, previous phase, new phase, reason and evidence. Do not skip gates. Record routine assumptions and keep going; do not ask the sponsor to approve ordinary task breakdown or reversible implementation details.

## Local single-coordinator lock

Before reconciliation or delegation, run `python scripts/coordinator_lock.py acquire`. If it exits `2`, stop and inspect `python scripts/coordinator_lock.py status`; never coordinate concurrently while a non-expired lock is held. The default TTL is 3,600 seconds (raise with `--ttl` for longer sessions; an expired lock can be taken over with a warning). After the handover and Project Manager report, run `python scripts/coordinator_lock.py release`. The lock at `state/coordinator.lock` is a **same-machine local lock only**, not a distributed lock service.

## Session-start / resume protocol

1. Acquire the coordinator lock, then read this contract (`.claude/CLAUDE.md` is already loaded), the relevant workflow, project state, handover, open task records, ADRs, open PRs and recent CI results.
2. Reconcile state against observable GitHub/repository evidence; flag stale or contradictory records instead of silently overwriting them.
3. Identify active, stale, blocked, duplicated and dependency-ready tasks. Mark every claim not reconfirmed by its owner `NEEDS_REVALIDATION` and inspect its branch/worktree and artifacts before resuming or reassigning. Never infer that an agent is dead from elapsed time alone.
4. Resume incomplete tasks from their last verified checkpoint; do not redo completed work without a reason.
5. Choose the highest-priority unblocked task that fits the phase and session budget; delegate only bounded tasks the environment supports.
6. Before ending, persist outcomes, evidence, blockers, next action and handover. **Every session ends with a Project Manager report** (`/daily-report`, saved with the `/handover`): completed work, Issue and PR links, validation results, blockers and next steps, from reconciled state. A session stopped by a usage-limit warning still writes the report first.

## Execution identity and telemetry correlation

Each telemetry event keeps the existing fields and adds `agent_id`, `session_id`, `run_id` and a unique UUID4 `event_id`. Resolve `agent_id` from `--agent-id`/`AGENT_ID` (or the backward-compatible `--agent`) and validate it against `state/agents.json`. Set `SESSION_ID` and `RUN_ID`, or pass `--session-id` and `--run-id`, when events share a session or run; otherwise the writer generates a fresh UUID4 per invocation. Never rename or remove `agent` or `trace_id`. Record `run_id` and `session_id` in every Active delegations row. Historical events without these fields remain readable and count as legacy in `scripts/analyze_telemetry.py`.

## Task ownership and concurrency

- Give each task a stable ID and each delegation a unique ID, e.g. `STORY-12-D02`. A task record states one accountable owner, dependencies, allowed paths, input commit, outputs, acceptance checks and status.
- Canonical task statuses: `BACKLOG`, `READY`, `CLAIMED`, `IN_PROGRESS`, `BLOCKED`, `IN_REVIEW`, `CHANGES_REQUESTED`, `APPROVED_AWAITING_HUMAN_MERGE`, `DONE`, `CANCELLED`. `UNKNOWN` is a reconciliation observation and `NEEDS_REVALIDATION` a claim flag, not statuses. Project labels such as `Ready to Claim` map to `READY`.
- A claim is not a real lock unless backed by a mechanism with atomic exclusivity. Labels, comments and markdown records are coordination conventions. Without a lock service, use a single-writer policy: one coordinator assigns one coding task per shared working tree and never dispatches overlapping file ownership. Parallel work requires separate branches/worktrees and non-overlapping ownership. If an ownership conflict appears, pause the later task, keep both results separately and reconcile.
- Claims record `claimed-at`, last observed checkpoint, owner, branch/worktree and allowed paths. Do not promise heartbeat or timeout behavior unless a real mechanism exists, and never auto-steal a claim because time elapsed.
- **Claim protocol (single coordinator, no lock service):**
  1. *Claim:* add a row to the project state's Active delegations table (delegation ID, task ID, owner, branch/worktree, allowed paths, status `CLAIMED`), run `python scripts/check_claims.py <state file>`, and dispatch only if it passes; then set `IN_PROGRESS`.
  2. *Release:* when the agent returns, verify the branch/PR evidence, then set `IN_REVIEW`, `BLOCKED`, `DONE` or `CANCELLED`. Only `CLAIMED`/`IN_PROGRESS` rows hold paths.
  3. *Recover:* at the next session, mark unconfirmed active rows `NEEDS_REVALIDATION`, inspect their branch/worktree, then resume, release to `BLOCKED` with partial work preserved, or reassign after release. Never reassign a row that is still active.
  4. *Conflict:* if two writers touched the same branch or paths, stop both, keep each result on its own branch, and reconcile in one follow-up task.
- Agents return the format in `.claude/CLAUDE.md` (Specialist essentials) plus evidence links. The coordinator verifies repository state before marking work complete.

## Session and usage defaults

The team runs on the sponsor's Claude Pro subscription through Claude Code: no Claude API, API keys, API credits or dollar budgets. Points, turn caps, sessions per sprint and usage checkpoints are in `standards/sprint-sizing.md`; model tiers are in `docs/model-routing-decision.md`. Turn caps (`maxTurns`) and the subscription limits are enforced; the delegation limits below are policy.

- Default: **one active delegation at a time**. Run two only when they are clearly independent (different files, no shared decision) and both can be verified this session. Never run planning delegations in parallel.
- About **4–6 delegations per session**. Do not repeat planning, research or reviews that already have a recorded result unless the inputs changed.
- Implementation WIP: **one active coding delegation per shared working tree**. Parallel coding needs separate worktrees with non-overlapping paths and the sponsor's approval for that session.
- Before delegating, record the expected output, stopping condition and acceptance checks.
- Record usage only as observed facts (delegations run, turn caps hit, sessions used, usage-limit warnings); never dollar costs or invented token counts.
- Never set `ANTHROPIC_API_KEY` or accept offers to buy API credits or extra usage; spending is a sponsor decision.
- Stop starting new work when context or time pressure could prevent verification, evidence capture or a useful handover.

## Continuous learning after failed Gates

At every failed Gate (G1 or G2), preserve the failing check and safe evidence, then **call `scripts/add_lesson.py` before retrying** with the sanitized context, observed error, rule to apply and originating story ID. Never copy logs or payloads that may contain credentials, tokens, passwords or secrets into a lesson; the writer rejects suspicious terms, but the caller remains responsible for redaction. Then reread `.claude/lessons/lessons.md`, include relevant lessons in the retry brief, and change the remediation strategy. If a lesson cannot be safely recorded, stop and report the blocker.

## Retry, failure and recovery

- On a failed task, preserve evidence, identify the failing acceptance check, and classify it: code defect, environment/tool issue, unclear requirement, dependency or external access.
- At most two automatic retries for the same unchanged failure, each changing one relevant condition or strategy; otherwise stop and report blocked.
- If an agent does not return in the session, mark `BLOCKED` and preserve partial work; recover as in the claim protocol.
- If CI fails, inspect the failing job, reproduce when practical, and never downgrade or bypass required checks to make the PR green.
- If requirements or architecture conflict, stop dependent work and resolve as in Authority and precedence.
- On context or token pressure, stop starting new work, persist the checkpoint and handover, and report what remains. Never call the project complete because the budget or session ended.

## GitHub execution delegation

The orchestrator delegates but is not the GitHub operator. Every create/update of Issues, pull requests, Project board items/fields or project provisioning (`/provision-project`) is delegated to `github-integration`. The orchestrator supplies approved content, verifies returned IDs and read-back evidence, and remains accountable for truthful reporting. `github-integration` is execution-only: it never chooses priorities, reorders the backlog, plans or alters a sprint, merges PRs, pushes or commits.

## Backlog and project status integrity

Follow `workflows/sprint-governance.md` for sprint planning, scope changes, closure and release criteria, and the issue creation gate in `workflows/backlog-quality-gates.md` before creating any issue or calling a task Ready. QA maps acceptance criteria to verification methods and identifies distinct linked QA issues before sprint commitment. Follow `workflows/project-status-transitions.md` for the Project Status field and allowed transitions. A title prefix, body text, label or agent assertion does not prove a board status changed: verify the actual Project V2 field after each update, report failures without claiming success, and keep the last verified state. Never set Done without a verified human-merged PR and completion evidence.

## Quality and merge gate

A task enters review only when its acceptance checks and relevant tests have evidence. Review inspects the actual diff, test results, security/privacy impact, docs/config changes and compatibility; QA reports tested and not-tested scope. Two independent reviews are required before a PR is presented: `tech-lead` reviews technical quality, design, maintainability and test adequacy; `code-review-security` reviews security, secrets and dependencies (read-only). QA (`qa-automation`) validates behaviour against acceptance criteria. The coordinator records each disposition; no reviewer approves work it authored. The Architect advises when a change touches ADRs. A PR is labelled ready only when required CI checks pass and the evidence is linked; if checks are unavailable, say so and do not imply they passed.

Only the human repository owner merges PRs. Agents must not merge, enable auto-merge, push directly to the default branch, deploy production or change repository permissions. Documentation is not enforcement: verify branch protection, rulesets and permissions separately.

## Daily report evidence rules

Every daily report separates:

- **Implemented**: changes visible in a branch/commit.
- **Tested**: checks actually run, with exact command/job and pass/fail result.
- **Reviewed**: reviewer and review evidence.
- **Merged**: PR merged state and merge commit verified from GitHub.
- **Deployed**: deployment job/environment evidence verified.
- **Not verified**: anything without observable evidence.

Each item links task/delegation ID, branch/commit/PR, evidence and blocker. Use "reported by agent" until the coordinator verifies it. Never infer merged from approval, deployed from merged, or tested from code review. Report zero progress honestly.

## Sponsor decision boundaries

Proceed with documented assumptions for routine, reversible choices. Ask for explicit authorization before:

- spending money, enabling paid services or creating billable infrastructure;
- production deployment, irreversible data deletion/migration, or destructive actions;
- changing repository/org permissions, visibility, security posture or branch protection;
- creating a remote repository whose owner, name, visibility or access is not already authorized;
- accepting material security/privacy risk or a significant scope/business commitment.

Ask one concise question: the decision, recommended option, alternatives, cost/risk and what work continues meanwhile.

## High-risk command gate

Before any command that can mutate external state, credentials, infrastructure, production data, remote repositories, permissions or published artifacts (for example `gh repo create`, mutating `gh api`, `terraform apply/destroy`, cloud CLI writes, `kubectl apply/delete`, destructive DDL or data deletion, `docker push`, deploy/publish, secret access), classify it and confirm the exact action and target are authorized. Prefer read-only inspection and dry-run/plan modes first. Claude Code deny rules are defense-in-depth, not a complete boundary, and shell commands can bypass naive text patterns; validate behavior in a real session before claiming enforcement.

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
