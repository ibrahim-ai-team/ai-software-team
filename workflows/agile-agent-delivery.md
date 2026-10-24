# Agile delivery workflow for Claude Code agents

## Operating model and accountability

- The Product Owner owns product discovery, requirements, user stories, acceptance criteria, and backlog priority. The user who provides the initial idea is the project sponsor/supervisor, not the day-to-day Product Owner.
- The Project Manager / Scrum Master is accountable for the delivery plan, sprint plan, story sequencing, dependencies, work in progress, follow-ups, status accuracy, risks, and daily report.
- `agile-orchestrator` (the main session, `claude --agent agile-orchestrator`) coordinates active work and remains accountable for integration and truthful reporting. A Project Manager subagent is a role invoked by the orchestrator, not a continuously running background service.
- The Tech Lead (`tech-lead`) splits Ready stories into small, independent tasks, owns implementation standards and performs the technical review of each PR.
- GitHub Issues are the durable record for backlog items, acceptance criteria, decisions, blockers, delegation summaries, and links to code/evidence.
- GitHub Projects is the planning board for the sprint. Keep status, priority, iteration, estimate, and owner visible when configured.
- GitHub does not automatically know which local subagent was called, what it returned, or whether a local test ran unless that is recorded.
- Every implementation task uses an isolated branch. Use a separate Git worktree per concurrently running coding agent where practical.
- `ci-verifier` executes only its closed allowlist of read-only verification commands and returns factual JSON; `code-review-security` (read-only, no shell) judges that evidence against the diff. `tech-lead` reviews technical quality and `qa-automation` validates behaviour. The coordinator records review disposition; the reviewer does not approve its own implementation. The repository owner/user alone performs the final merge; agents must never merge PRs or configure automation to merge on the user's behalf.

## End-to-end workflow from an idea

1. **Activate project:** When the user gives an application idea and asks the team to build it, use workflows/project-bootstrap.md. Do not treat a vague brainstorming request as implementation authorization.
2. **Discover and specify:** Product Owner and Business Analyst identify target users, problems, workflows, functional/non-functional requirements, risks, assumptions, and unresolved questions. Ask the user only for material decisions that cannot safely be inferred; document assumptions rather than blocking on routine details.
3. **Design:** Architect compares viable architecture and technology options against the requirements, documents the recommendation and trade-offs, and creates ADRs for consequential decisions.
4. **Prepare delivery:** Project Manager builds the prioritized backlog, dependencies, estimates, delivery slices, and sprint plan. QA contributes acceptance and test strategy early. DevOps proposes the required environments and CI/CD.
5. **Set up the project:** Create repositories, project boards, cloud resources, paid services, permissions, or secrets only when the required target and authorization are clear. Never invent credentials or bypass missing access.
6. **Implement incrementally:** Project Manager selects Ready work and prepares bounded delegation records, tracks claims and dependencies, and flags stale or blocked work. `agile-orchestrator` dispatches each task and owns branches, PRs and GitHub writes. Specialists work on the assigned branch and report exact checks and evidence.
7. **Verify and review:** QA and reviewers inspect evidence and actual diffs. Keep implemented, tested, merged, and deployed as separate states.
8. **Report and resume:** Reconcile every delegation, update Issues/Project status and project-state summary, publish the daily report, and leave a session handover. On the next session, read durable state before starting new work.

## Mechanical validation gates (mandatory)

Follow `standards/validation-gates.md`. Gates are agent-produced technical evidence; CP1–CP4 remain human approvals as defined in `standards/human-in-the-loop.md`. Never substitute one for the other.

1. **Before any coding delegation:** obtain human CP1 (plan) and CP2 (architecture) approvals with `python scripts/check_approvals.py --story <story> --checkpoint CP1` and `--checkpoint CP2`. Then require the plan review Gate 1: `python scripts/check_gates.py --story <story> --gate G1`. If any command returns non-zero, stop and request the missing approval or gate evidence. No coder may start without both CP1/CP2 and a passing G1.
2. **After implementation, before merge readiness:** (1) delegate to `ci-verifier` for factual JSON evidence; (2) pass the JSON and actual diff to `code-review-security` for judgment; (3) persist G2 only if the reviewer approves, then run `python scripts/check_gates.py --story <story> --gate G2`. A skipped, failed, missing, or disputed mandatory check blocks G2. If verifier and reviewer diverge, escalate to the human sponsor at CP3. The verifier never persists to `.claude/gates/`; the orchestrator persists only after review.
3. **Before merge:** require human CP3 via `python scripts/check_approvals.py --story <story> --checkpoint CP3` after G2 passes. Only the human repository owner merges.
4. **Before release tagging:** require G2 evidence for the release candidate and human CP4 as applicable; follow the release checkpoint policy.

Required ordered flow: `CP1 → G1 → code → G2 → CP3 → merge`. CP2 is also mandatory before implementation under the HITL standard. The orchestrator checks the relevant gate before every lifecycle transition and never fabricates result files.

## Sprint closure and ROI reporting

At the end of every sprint, the Project Manager records per-story agent minutes, token counts, and estimated equivalent human hours in `.claude/metrics/sprint-<N>.json` using the schema in `.claude/metrics/README.md`. The orchestrator runs `python scripts/roi_report.py --sprint <N>` and includes the generated Markdown in the sprint review. If the input is missing or invalid, report the error and resolve the metrics; do not invent figures or claim a completed ROI report. The report is local-only and uses the ratio `estimated human cost / token cost`; it does not represent net profit and excludes infrastructure/runtime costs.

## User involvement

The team should run routine planning and execution without requiring the user to assign every task or approve every sprint item. The Project Manager may continue with already-scoped, reversible work. Ask for user input only when:

- a material product question has no safe, documented assumption;
- requirements conflict or a business decision changes expected behavior;
- an action would spend money, enable a paid service, change access/visibility, deploy to production, destroy data, or make an irreversible change;
- an external repository/resource needs to be created and its owner, visibility, or authorization is not established;
- the team is blocked and cannot resolve the issue within the approved scope.

The user receives visibility and retains final PR merge authority. A request to build an application authorizes planning and routine implementation within available project/repository scope; it does not authorize paid services, production deployment, or other protected actions.

## Backlog quality and QA planning (mandatory)

Before any issue enters `Ready`, follow `workflows/backlog-quality-gates.md`. Create issues with the matching form under `.github/ISSUE_TEMPLATE/`; do not rely on title prefixes for metadata. The PM owns the Definition of Ready gate, while QA maps each acceptance criterion to verification and creates a separate linked `[QA]` issue when the work is a distinct deliverable. A confirmed product defect requiring separate remediation becomes a linked `[BUG]` issue. If tests reasonably fit the implementation task, keep them there and record the rationale instead of creating unnecessary tickets. Missing acceptance criteria, priority, dependencies, estimates/refinement plan, QA mapping, or evidence expectations keep the item in Backlog.

## Issue lifecycle

1. **Backlog** — captured, not committed to a sprint.
2. **Ready** — clear acceptance criteria, test expectations, and dependencies identified.
3. **In Progress** — one primary implementation owner has claimed the task.
4. **In Review** — a PR is open, linked to the issue, and evidence is supplied.
5. **Changes Requested** — the `code-review-security` report or coordinator verification found specific issues that need fixing.
6. **Approved — Awaiting Human Merge** — The coordinator recorded review disposition as approved for the current revision and required checks pass.
7. **Done** — the user merged the PR and the issue was verified/closed.
8. **Blocked** — blocker, impact, attempted resolution, and needed decision/dependency are recorded.

Never mark an issue Done merely because local implementation or approval exists. Never leave a blocked task silently In Progress.

## Project Manager daily operating loop

At the start of each active session:

1. Read the project status summary, latest handover, active sprint, open Issues, open PRs, recent CI results, unresolved review comments, blockers, and pending user decisions.
2. Reconcile these sources; do not assume yesterday's conversation is the only source of truth.
3. Select the next highest-priority Ready work based on sprint goal, dependencies, risk, and work-in-progress limits.
4. Delegate bounded tasks with unique delegation IDs, clear deliverables, acceptance checks, and file ownership.
5. Follow up on outputs, inspect evidence, request fixes when necessary, and update durable records.

Before ending a session:

1. Reconcile every delegation ID to a state: completed, partial, in progress, blocked, failed, cancelled, or rejected.
2. Link outputs to Issues, PRs/commits, ADRs, CI/test evidence, or follow-up tasks.
3. Update issue/project statuses and the current project-state summary.
4. Publish the daily report using templates/daily-project-report-template.md.
5. Update templates/session-handover-template.md or a project-specific equivalent with the next 1–3 actions.
6. Clearly identify PRs awaiting the user. Never merge them.

## Delegation and traceability rules

Follow docs/agent-traceability.md. Assign IDs such as TASK-142-D01 for each subagent assignment. Record objective, input/context, expected output, acceptance checks, file ownership, status, reported outcome, coordinator disposition, evidence, and next action. Record meaningful state changes rather than every internal step. A subagent saying "done" is not proof of integration, correctness, or passing tests.

## Sprint cadence

Sprints last two weeks unless the project records a different length. The `project-manager` role owns routine sprint planning and tracking. The `product-owner` maintains product priorities; `software-architect` and `tech-lead` check technical feasibility; `qa-automation` plans verification. The main session remains the actual delegation coordinator. Record sprint goals and changes in GitHub. Do not block routine, already-scoped work on repeated user approvals. At sprint end, report merged outcomes separately from open PRs and unfinished work.

## Task claiming and local execution

Before coding, the developer agent must:

1. Read the issue, acceptance criteria, linked decisions, repo instructions, and relevant implementation.
2. Confirm the issue is Ready, dependencies are met, and no other agent owns implementation.
3. State a short plan and expected files/checks.
4. Create a branch named feat/<issue-number>-<short-name>, fix/<issue-number>-<short-name>, or chore/<issue-number>-<short-name>.
5. If another agent is using the same checkout, use a separate worktree or wait. Never concurrently edit the same working tree.
6. Make the smallest coherent change; do not refactor unrelated code.
7. Run relevant tests, lint, type checks, and static validation available locally. Report exact commands and results; never fabricate checks.
8. Commit and push the branch, then open a PR linked to the issue. If a required check cannot run, disclose why and mark it as not run.

Task claiming is a coordination protocol implemented by the main session and issue/status updates; a GitHub Issue alone does not lock an agent.

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

Review the current PR diff, not merely the developer summary. Verify correctness, acceptance criteria, architecture, test quality, security/privacy, dependency changes, maintainability, CI status, evidence, and unresolved review threads. If changes are needed, request changes with actionable findings, severity, affected file/line, and expected resolution. Approve only when the current revision is acceptable and evidence supports it. If formal GitHub reviews are unavailable, label the report as a comment and do not claim a formal approval. Approval is not merge authorization.

## Framework and architecture improvement proposals

Proposals must explain the current problem and evidence, expected benefit/measurement, alternatives including doing nothing, compatibility/security/maintenance/migration/cost/token/rollback risks, affected artifacts, and proof-of-concept success criteria. Record consequential accepted decisions as ADRs. Seek user approval for material risk/cost/access changes; do not turn speculative improvements into sprint work automatically.

## Automation boundaries

Safe candidates: static validation, explicit status updates, sprint summaries, and PR-ready notifications. Human-controlled actions: final merge, production deployment, destructive/irreversible operations, permission changes, secret exposure, and spending/enabling paid services. CI and read-only reviewer findings support the user's decision; neither replaces it.
