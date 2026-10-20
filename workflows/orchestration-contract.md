# Orchestration Contract

## Purpose and limits
This contract defines the repeatable control loop for a Claude Code session. It is a protocol, not a background service, distributed lock manager, or proof that Claude Code can discover or delegate to every profile. The coordinator of record is `agile-orchestrator`, started as the main session with `claude --agent agile-orchestrator`. If a session is started without it, the top-level session follows this same contract. Delegation is hub-and-spoke: only the orchestrator has the `Agent` tool; specialists return results to it and never call each other. Work stops when the session stops unless an independently configured scheduler invokes it.

## Canonical state and precedence
For each project, maintain a durable project state file in the project repository (recommended: `docs/project-state.md`) and task records in GitHub Issues when available. Keep sensitive values out of state files.

Precedence when records disagree:
1. Actual repository contents, commits, PR state, and CI results for code/check facts.
2. Explicit sponsor decisions and recorded ADRs for approved decisions.
3. Canonical task/issue status for task state.
4. Delegation records and activity log for agent progress claims.
5. Chat history and unverified agent claims are context only, never proof.

Every project state snapshot must include: project ID/name, last reconciled timestamp (UTC), current phase, goal/scope, approved decisions and ADR links, assumptions, task IDs/status/owner/dependencies, active delegation IDs, PRs, CI/test evidence, blockers, sponsor decisions needed, next actions, and last known commit. If GitHub is unavailable, use a local state file and say that remote sync is unavailable.

## Threat-model checkpoint

During `ARCHITECTURE`, before implementation begins, require a documented threat-model checkpoint whenever the system handles authentication/authorization, personal or sensitive data, external integrations/webhooks, file uploads, payment flows, secrets, or privileged operations. Use `.claude/skills/security-threat-modelling/SKILL.md`. Record assets, trust boundaries, abuse cases, mitigations, residual risks, and verification tasks. If the scope has no meaningful security-sensitive data flow, record `NOT APPLICABLE` with a short rationale.

## State machine
Project phases:
- `DISCOVERY`: capture idea, goals, users, outcomes, constraints.
- `SPECIFICATION`: PO/BA produce requirements, journeys, edge cases, acceptance criteria, NFRs, assumptions and open questions.
- `ARCHITECTURE`: Architect compares options and records recommended architecture and material trade-offs; Tech Lead validates buildability and sets implementation standards.
- `BACKLOG_READY`: PM (Scrum Master) builds the prioritized backlog and a two-week sprint (default length); Tech Lead splits stories into small, path-bounded tasks; QA/DevOps contribute verification and delivery needs.
- `AWAITING_SPONSOR_DECISION`: pause only for material business direction, budget/spending, access/visibility, security-risk acceptance, destructive actions, production release, or other irreversible commitment.
- `DELIVERY`: execute bounded Ready tasks.
- `INTEGRATION_REVIEW`: integrate compatible outputs, run checks, QA and security review.
- `AWAITING_HUMAN_MERGE`: PR is ready, evidence and review are recorded; human owner merges.
- `MAINTENANCE`: resume from reconciled state, repair blockers, continue next priority.
- `BLOCKED`: no safe task can progress; report exact blocker and requested action.
- `COMPLETE`: only when stated scope and Definition of Done are verified; not merely because a session ended.

Transitions must be recorded with timestamp, previous phase, new phase, reason, and evidence. Do not skip gates. Routine assumptions should be recorded and progress should continue; do not repeatedly ask the sponsor to approve ordinary task breakdown or reversible implementation details.

## Session-start / resume protocol
1. Read this contract, `.claude/CLAUDE.md`, the relevant workflow, project state, handover, open task records, ADRs, open PRs and recent CI results.
2. Reconcile the state against observable GitHub/repository evidence; flag stale or contradictory records rather than silently overwriting them.
3. Identify active, stale, blocked, duplicated, and dependency-ready tasks. Claims are session-scoped coordination records, not locks or heartbeats. At the start of each new coordinator session, any claim not reconfirmed by its owner must be marked `NEEDS_REVALIDATION`; inspect branch/worktree and artifacts before resuming or reassigning. Never infer that an agent is dead from elapsed time alone.
4. Resume incomplete tasks from their last verified checkpoint. Do not redo completed work without a reason.
5. Choose the highest-priority unblocked task that fits the current phase and session budget; delegate only if the task is bounded and the environment supports the required agent/tool behavior.
6. Before ending, persist outcomes, evidence, blockers, next action and handover; update the daily report from reconciled state.

## Task ownership and concurrency
- Give each task a stable ID and each delegation a unique ID, e.g. `STORY-12-D02`.
- Task record must state one accountable owner, dependencies, allowed paths/files, input commit, outputs, acceptance checks, and status.
- Canonical task statuses: `BACKLOG`, `READY`, `CLAIMED`, `IN_PROGRESS`, `BLOCKED`, `IN_REVIEW`, `CHANGES_REQUESTED`, `APPROVED_AWAITING_HUMAN_MERGE`, `DONE`, `CANCELLED`. `UNKNOWN` is a reconciliation observation only; `NEEDS_REVALIDATION` is a claim flag, not a task status. GitHub Project labels such as `Ready to Claim` must map to canonical `READY` in the task record.
- A claim is not a real lock unless backed by a mechanism with atomic exclusivity. GitHub labels/comments and markdown records are coordination conventions, not distributed locks. If no lock service exists, use a single-writer policy: one coordinator assigns one coding task per shared working tree, records owner/branch, and does not dispatch overlapping file ownership. Parallel work requires separate branches/worktrees and non-overlapping ownership.
- Never let two coding agents edit the same working tree or the same owned files concurrently. If ownership conflict appears, pause the later task, preserve both results separately, and ask the coordinator to reconcile.
- Claims record `claimed-at`, last observed checkpoint, owner, branch/worktree, and allowed paths. Do not promise heartbeat/timeout behavior unless a real mechanism exists. At the next coordinator session, reconfirm ownership and inspect artifacts before resuming or reassigning; do not auto-steal a claim solely because time elapsed.
- **Claim protocol (single coordinator, no lock service):**
  1. *Claim:* the coordinator adds a row to the project state file's Active delegations table (delegation ID, task ID, owner, branch/worktree, allowed paths, status `CLAIMED`), runs `python scripts/check_claims.py <state file>`, and dispatches only if it passes. Then it sets `IN_PROGRESS`.
  2. *Release:* when the agent returns, the coordinator verifies the branch/PR evidence, then sets the row to `IN_REVIEW`, `BLOCKED`, `DONE` or `CANCELLED`. Only `CLAIMED`/`IN_PROGRESS` rows hold paths.
  3. *Recover:* at the next coordinator session, mark unconfirmed active rows `NEEDS_REVALIDATION`, inspect their branch/worktree, then either resume, release to `BLOCKED` with the partial work preserved, or reassign after release. Never reassign a row that is still active.
  4. *Conflict:* if two writers touched the same branch or paths, stop both, keep each result on its own branch, and reconcile in one follow-up task.
- Agents return: delegation ID, status, changed paths, commit/branch, checks actually run and their results, evidence links, risks, unresolved items, and next recommendation. The coordinator verifies repository state before marking work complete.

## Session and cost budget defaults

Sprint budgets, story points, per-role turn caps and the 70%/90% budget thresholds are defined in `standards/sprint-sizing.md`. Turn caps (`maxTurns`) are enforced by Claude Code; budgets and thresholds are policy.

- Default maximum: **3 active delegations per coordinator session**, including research/review work. The coordinator may lower this for complex tasks or a tight context budget; raise it only when the work is independent and verification capacity remains.
- Default implementation WIP: **one active coding delegation per shared working tree**. Parallel coding is allowed only in separate worktrees/branches with non-overlapping allowed paths; default maximum is **2 concurrent coding delegations** unless the human owner approves a higher limit for a specific session.
- Before delegating, record the task's expected output, stopping condition, and verification budget. Prefer the least costly model that is actually available and suitable in the current runtime; never assume model IDs or pricing.
- Record observed token use, cost, and duration only when the runtime exposes reliable values. Otherwise record `unavailable`; do not fabricate estimates as measurements.
- Stop starting new work when context or time pressure could prevent verification, evidence capture, or a useful handover.

## Retry, failure and recovery
- On a failed task, preserve logs/evidence, identify the failing acceptance check, and classify as code defect, environment/tool issue, unclear requirement, dependency, or external access.
- Permit at most two automatic retries for the same unchanged failure. Each retry must change one relevant condition or strategy; otherwise stop and report blocked. Do not loop indefinitely or burn context/tokens.
- If an agent fails to return in the current session, mark `BLOCKED` and preserve partial work. Use `UNKNOWN` only as a reconciliation observation, not a task status. At session resume, inspect the branch/worktree and reconfirm ownership before reassignment; document the handover.
- If CI fails, inspect the failing job and logs, reproduce when practical, and never downgrade or bypass required checks merely to make the PR green.
- If requirements or architecture conflict, stop dependent work, record the conflict and impact, and resolve via the role owner or sponsor decision gate.
- On context/token pressure, stop starting new work, persist the checkpoint and handover, and report what remains. Never claim the overall project is complete because the budget or session ended.

## Backlog and project status integrity

Follow `workflows/backlog-quality-gates.md` before a task is considered Ready. QA must map acceptance criteria to verification methods and identify distinct linked QA issues before sprint commitment. Follow `workflows/project-status-transitions.md` for the canonical GitHub Projects Status field and allowed transitions. A title prefix, issue body text, label, or agent assertion does not prove a board status changed. The coordinator must verify the actual Project V2 field after a status update. Report status-update failures without claiming success; keep the last verified state. Never set Done without a verified human-merged PR and completion evidence.

## Quality and merge gate
A task can enter review only when its acceptance checks and relevant tests have evidence. Review must inspect the actual diff, test results, security/privacy impact, docs/config changes, and compatibility. QA reports tested and not-tested scope. Two independent reviews are required before a PR is presented: `tech-lead` reviews technical quality, design, maintainability and test adequacy; `code-review-security` reviews security, secrets and dependencies (read-only). QA (`qa-automation`) validates behaviour against acceptance criteria. The coordinator records each disposition in the delegation/PR record; no reviewer approves work it authored. The Architect advises when a change touches ADRs. A PR may be labelled ready only when required CI checks pass and the evidence is linked; if checks are unavailable, state that explicitly and do not imply they passed.

Only the human repository owner merges PRs. Agents must not merge, enable auto-merge, push directly to the default branch, deploy production, or change repository permissions. Documentation is not enforcement: verify GitHub branch protection/rulesets and repository permissions separately.

## Daily report evidence rules
Every daily report separates:
- **Implemented**: changes visible in a branch/commit.
- **Tested**: checks actually run, with exact command/job and pass/fail result.
- **Reviewed**: reviewer and review evidence.
- **Merged**: PR merged state and merge commit verified from GitHub.
- **Deployed**: deployment job/environment evidence verified.
- **Not verified**: anything for which observable evidence is absent.

Each item links task/delegation ID, branch/commit/PR, evidence, and blocker. Use "reported by agent" until the coordinator independently verifies it. Never infer merged from PR approval, deployed from merged, or tested from code review. Report zero progress honestly when appropriate.

## Sponsor decision boundaries
Proceed with documented assumptions for routine and reversible choices. Pause and ask for explicit authorization before:
- spending money, enabling paid services or creating billable infrastructure;
- production deployment, data deletion/migration with irreversible impact, or destructive actions;
- changing repository/org permissions, visibility, security posture or branch protection;
- creating a remote repository when owner, name, visibility, or access scope is not already explicitly authorized;
- accepting material security/privacy risk or making a significant scope/business commitment.

Ask one concise question containing the decision, recommended option, alternatives, cost/risk and what work can continue safely meanwhile.

## High-risk command gate

Before running any command that can mutate external state, credentials, infrastructure, production data, remote repositories, permissions, or published artifacts, the coordinator must classify the command and check explicit authorization. Examples include `gh repo create`, mutating `gh api` calls, `terraform apply/destroy`, cloud CLI writes, `kubectl apply/delete`, database destructive DDL/data deletion, `docker push`, deployment/publish commands, and secret/credential access. Do not run such commands unless the exact action and target are authorized. Prefer read-only inspection and dry-run/plan modes first. Existing Claude Code deny rules are defense-in-depth only; they are not a complete security boundary, and shell commands can bypass naive text patterns. Validate actual behavior in a real Claude Code session before claiming enforcement.

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
