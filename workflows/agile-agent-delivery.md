# Agile delivery workflow for Claude Code agents

Coordination, phases, session start/end, authority and sponsor boundaries are defined once in `workflows/orchestration-contract.md`; this workflow adds the delivery-specific rules.

Contents: before coding → [gates](#mechanical-validation-gates-mandatory), [task claiming](#task-claiming-and-local-execution), [backlog readiness](#backlog-quality-and-qa-planning-mandatory); before a PR → [readiness checklist](#pull-request-readiness-checklist), [review protocol](#coordinator-review-protocol); sprint end → [closure and ROI](#sprint-closure-and-roi-reporting), [cadence](#sprint-cadence); reference → [accountability](#operating-model-and-accountability), [workflow from an idea](#end-to-end-workflow-from-an-idea), [user involvement](#user-involvement), [issue lifecycle](#issue-lifecycle), [daily loop](#project-manager-daily-operating-loop), [traceability](#delegation-and-traceability-rules), [improvement proposals](#framework-and-architecture-improvement-proposals), [automation boundaries](#automation-boundaries).

## Operating model and accountability

- The Product Owner owns discovery, requirements, stories, acceptance criteria and backlog priority. The user who provides the idea is the sponsor/supervisor, not the day-to-day Product Owner.
- The Project Manager / Scrum Master owns the delivery and sprint plan, sequencing, dependencies, WIP, follow-ups, status accuracy, risks and the daily report. It is a role the orchestrator invokes, not a background service.
- `agile-orchestrator` (the main session) coordinates active work and remains accountable for integration and truthful reporting. `tech-lead` splits Ready stories into small tasks, owns implementation standards and performs the technical review of each PR.
- GitHub Issues are the durable record for backlog items, acceptance criteria, decisions, blockers, delegation summaries and evidence links; GitHub Projects is the sprint board. GitHub does not know which subagent ran, what it returned or whether a local test ran unless that is recorded.
- Every implementation task uses an isolated branch, and a separate worktree per concurrently running coding agent where practical.
- `ci-verifier` runs only its closed allowlist of read-only commands and returns factual JSON; `code-review-security` (read-only, no shell) judges that evidence against the diff; `tech-lead` reviews technical quality and `qa-automation` validates behaviour. No reviewer approves its own work. Only the repository owner merges; agents never merge or configure automation to merge.

## End-to-end workflow from an idea

1. **Activate:** when the user asks the team to build an application idea, use `workflows/project-bootstrap.md`. Vague brainstorming is not implementation authorization.
2. **Discover and specify:** PO and BA identify users, problems, workflows, functional and non-functional requirements, risks, assumptions and open questions. Ask the user only for material decisions that cannot safely be inferred.
3. **Design:** the Architect compares options against the requirements, documents the recommendation and trade-offs, and writes ADRs for consequential decisions.
4. **Prepare delivery:** the PM builds the prioritized backlog, dependencies, estimates, slices and sprint plan; QA contributes test strategy early; DevOps proposes environments and CI/CD.
5. **Set up:** create repositories, boards, cloud resources, paid services, permissions or secrets only when the target and authorization are clear. Never invent credentials or bypass missing access.
6. **Implement incrementally:** the PM selects Ready work and prepares bounded delegation records; the orchestrator dispatches each task and delegates all GitHub operations to `github-integration`. Specialists work on the assigned branch and report exact checks and evidence.
7. **Verify and review:** QA and reviewers inspect evidence and the actual diff. Implemented, tested, merged and deployed stay separate states.
8. **Report and resume:** reconcile every delegation, update Issues/Project and the project state, publish the daily report and leave a handover.

## Mechanical validation gates (mandatory)

Follow `standards/validation-gates.md`. Gates are agent-produced technical evidence; CP1–CP4 remain human approvals (`standards/human-in-the-loop.md`). Never substitute one for the other.

1. **Before any coding delegation:** obtain human CP1 (plan) and CP2 (architecture) with `python scripts/check_approvals.py --story <story> --checkpoint CP1` and `--checkpoint CP2`, then require Gate 1: `python scripts/check_gates.py --story <story> --gate G1`. Any non-zero result stops work until the approval or evidence exists.
2. **After implementation, before merge readiness:** (1) delegate to `ci-verifier` for factual JSON evidence; (2) pass the JSON and actual diff to `code-review-security` for judgment; (3) persist G2 only if the reviewer approves, with the `commit` `ci-verifier` tested, then run `python scripts/check_gates.py --story <story> --gate G2 --commit <PR head SHA>`; a commit pushed after verification needs a new G2. A skipped, failed, missing or disputed mandatory check blocks G2. If verifier and reviewer diverge, escalate to the human sponsor at CP3. The verifier never writes to `.claude/gates/`; the orchestrator persists only after review.
3. **Before merge:** require human CP3 via `python scripts/check_approvals.py --story <story> --checkpoint CP3` after G2 passes. Only the human repository owner merges.
4. **Before release tagging:** require G2 evidence for the release candidate and human CP4 as applicable.

Required order: `CP1 → G1 → code → G2 → CP3 → merge`, with CP2 also mandatory before implementation. Check the relevant gate before every lifecycle transition and never fabricate result files.

## Sprint closure and ROI reporting

At sprint end, the PM records per-story agent minutes, token counts and estimated human hours in `.claude/metrics/sprint-<N>.json` (schema: `.claude/metrics/README.md`). The orchestrator runs `python scripts/roi_report.py --sprint <N>` and includes the generated Markdown in the sprint review. If input is missing or invalid, report the error and fix the metrics; never invent figures or claim a completed report. The report is local-only and uses the ratio `estimated human cost / token cost`; it is not net profit and excludes infrastructure costs.

## User involvement

Routine planning and execution run without the user assigning tasks or approving sprint items; ask only in the cases listed under Sponsor decision boundaries in `workflows/orchestration-contract.md`, or when the team is blocked within the approved scope. A request to build an application authorizes planning and routine implementation within the available repository scope, not paid services, production deployment or other protected actions. The user keeps visibility and final merge authority.

## Backlog quality and QA planning (mandatory)

Before any issue enters `Ready`, follow `workflows/backlog-quality-gates.md`. Create issues with the matching form under `.github/ISSUE_TEMPLATE/`; never rely on title prefixes for metadata. The PM owns the Definition of Ready gate. QA maps each acceptance criterion to verification and creates a separate linked `[QA]` issue only for a distinct deliverable; tests that fit the implementation task stay there with the rationale recorded. A confirmed defect needing separate remediation becomes a linked `[BUG]` issue. Missing acceptance criteria, priority, dependencies, estimate or refinement plan, QA mapping or evidence expectations keep the item in Backlog.

## Issue lifecycle

1. **Backlog** — captured, not committed to a sprint.
2. **Ready** — clear acceptance criteria, test expectations and dependencies identified.
3. **In Progress** — one primary implementation owner has claimed the task.
4. **In Review** — a PR is open, linked to the issue, with evidence supplied.
5. **Changes Requested** — review or coordinator verification found specific issues to fix.
6. **Approved — Awaiting Human Merge** — review disposition approved for the current revision and required checks pass.
7. **Done** — the user merged the PR and the issue was verified and closed.
8. **Blocked** — blocker, impact, attempted resolution and needed decision recorded.

Never mark Done because local implementation or approval exists, and never leave a blocked task silently In Progress. The board's allowed transitions are in `workflows/project-status-transitions.md`.

## Project Manager daily operating loop

At session start and end, follow the session-start/resume protocol in `workflows/orchestration-contract.md`. In addition, before ending: reconcile every delegation ID to completed, partial, in progress, blocked, failed, cancelled or rejected; link outputs to Issues, PRs/commits, ADRs, CI evidence or follow-up tasks; publish the daily report (`templates/daily-project-report-template.md`); update the handover (`templates/session-handover-template.md`) with the next 1–3 actions; and list PRs awaiting the user, never merging them.

## Delegation and traceability rules

Follow `docs/agent-traceability.md`. Give each subagent assignment an ID such as TASK-142-D01 and record objective, inputs, expected output, acceptance checks, file ownership, status, reported outcome, coordinator disposition, evidence and next action. Record meaningful state changes, not every internal step. A subagent saying "done" is not proof of integration, correctness or passing tests.

## Sprint cadence

Sprints last two weeks unless the project records a different length; planning, scope and closure rules are in `workflows/sprint-governance.md`. At sprint end, report merged outcomes separately from open PRs and unfinished work.

## Task claiming and local execution

Before coding, the developer agent:

1. Reads the issue, acceptance criteria, linked decisions, repo instructions and relevant code.
2. Confirms the issue is Ready, dependencies are met and no other agent owns it.
3. States a short plan with expected files and checks.
4. Works on a branch named `feat/`, `fix/` or `chore/` + `<issue-number>-<short-name>`, in a separate worktree if another agent uses the same checkout. Never edit a working tree concurrently.
5. Makes the smallest coherent change, without unrelated refactoring.
6. Runs the relevant tests, lint, type checks and static validation; reports exact commands and results, and marks anything not run with the reason.
7. Commits and pushes the branch and opens a PR linked to the issue, when authorized.

Claiming is a coordination protocol run by the main session; a GitHub Issue alone does not lock an agent.

## Pull request readiness checklist

- [ ] PR title is clear and issue is linked.
- [ ] Scope matches the task; unrelated changes are excluded.
- [ ] Acceptance criteria are mapped to implementation and evidence.
- [ ] Relevant tests were added/updated and actual commands/results are reported.
- [ ] Relevant lint/build/type checks were run or explicitly marked not run with reason.
- [ ] Security, secrets, permissions, data handling, and error handling were considered.
- [ ] Documentation/configuration/migration changes are included when needed.
- [ ] Known limitations, risks, and follow-up work are stated.
- [ ] No secrets, credentials, or generated clutter are included.
- [ ] PR has not been merged.

## Coordinator review protocol

Review the current PR diff, not the developer summary. Verify correctness, acceptance criteria, architecture, test quality, security/privacy, dependency changes, maintainability, CI status, evidence and unresolved threads. Request changes with severity, file/line and expected resolution. Approve only when the current revision and its evidence are acceptable. If formal GitHub reviews are unavailable, label the report a comment, not an approval. Approval is not merge authorization.

## Framework and architecture improvement proposals

A proposal explains the problem and evidence, expected benefit and how to measure it, alternatives including doing nothing, compatibility, security, maintenance, migration, cost, token and rollback risks, affected artifacts, and proof-of-concept success criteria. Record accepted consequential decisions as ADRs. Seek user approval for material risk, cost or access changes; speculative improvements never become sprint work automatically.

## Automation boundaries

Safe to automate: static validation, explicit status updates, sprint summaries, PR-ready notifications. Human-controlled: final merge, production deployment, destructive or irreversible operations, permission changes, secret exposure, spending or enabling paid services. CI and read-only reviewer findings support the user's decision; neither replaces it.
