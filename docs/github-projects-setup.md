# GitHub Projects setup for the AI team

This is a manual setup guide. It does not create a GitHub Project or modify repository settings automatically.

## Keep infrastructure and application planning separate

- **Infrastructure board:** keep the existing organization Project #1 for the `ai-software-team` repository. Use it for improving the agents, skills, workflows, security, and orchestration framework itself.
- **One board per real application:** when an application is initialized, create or reuse one organization Project for that product and link its related repositories (for example, API, web, mobile, and tests). Do not create empty application boards before there is a real product to plan.
- **One Project with several views:** do not create a separate Project for every sprint. Use iterations and saved views to separate the current sprint, next sprint candidates, and the full backlog.

Follow [the reusable per-application Project blueprint](per-app-project-blueprint.md) for required fields, seven recommended views, planning rules, and the new-application bootstrap checklist.

## Recommended infrastructure Project fields

Create or reuse these fields on the infrastructure board:

- **Status:** Backlog, Ready, In Progress, In Review, Changes Requested, Approved — Awaiting Human Merge, Blocked, Done.
- **Priority:** P0, P1, P2, P3.
- **Iteration:** two-week sprint iterations.
- **Estimate:** a small effort scale such as 1, 2, 3, 5, 8; split work estimated above 5 where practical.
- **Work type:** Story, Bug, Tech Debt, Framework Proposal, Documentation, Infrastructure, QA.
- **Owner:** responsible human or agent identity/label supported by your orchestration setup.
- **Dependencies:** use issue relationships or explicit links in the issue body.
- **Evidence / PR:** URL or text field for pull requests, CI runs, and test reports.

GitHub Projects features and field availability can vary by project type and account permissions; configure equivalent fields if names differ. Reuse existing fields rather than creating competing fields.

## Canonical status and transition rules

The Project V2 single-select `Status` field is the source of truth for board status; issue titles must not carry status prefixes as a second source of truth. Use `workflows/project-status-transitions.md` for permitted transitions, event triggers, and required evidence. Use `workflows/backlog-quality-gates.md` for Definition of Ready and QA decomposition. A manual setup guide is not automation: verify the actual project fields, options, view filters, and item status after configuration.

## Infrastructure board views

Recommended views for the infrastructure Project:

1. **Product Backlog:** all unfinished infrastructure work, sorted by priority.
2. **Sprint actif:** current two-week iteration, grouped by Status.
3. **Sprint prochain:** next iteration candidates in Backlog or Ready; not yet committed.
4. **Ready to Claim:** Ready issues with dependencies and estimate visible.
5. **QA & Review:** In Review, Changes Requested, and Approved — Awaiting Human Merge.
6. **Blocked:** Blocked issues with blocker details visible.
7. **Sprint Review:** current iteration grouped by Done versus unfinished work.

If existing views use other names, rename or map them intentionally; do not create duplicate views without checking first.

## Labels to add

Suggested issue labels: type:story, type:bug, type:tech-debt, type:framework-proposal, type:docs, type:qa, priority:P0, priority:P1, priority:P2, priority:P3, status:blocked, needs:decision, needs:acceptance-criteria.

Labels do not enforce access control or prove an agent has claimed a task. Treat them as visible metadata.

## Sprint ceremony

- **Sprint planning:** choose a goal, confirm Ready items and dependencies, estimate capacity, and report the commitment to the sponsor; seek approval only when it changes agreed scope, cost, risk or a deadline.
- **During sprint:** keep status current, surface blockers quickly, and avoid adding major scope without explicit approval.
- **Sprint review:** show merged outcomes and evidence; list unfinished tasks honestly.
- **Retrospective:** record one or two actionable process improvements as backlog issues.

## Important limitations

`.github/workflows/project-status.yml` updates one issue's Status on a selected Project (`project_owner`, default the repository owner; `project_number`, default 1). It finds the item from the issue side, so board size does not matter, validates the transition and reads the value back. It needs a `PROJECTS_TOKEN` secret with Projects read/write and runs only in the repository that holds the issue. Until a real update and read-back is recorded in `docs/verification-report.md`, treat it as untested.

GitHub Issues and Projects provide the board and durable task records, but they do not automatically coordinate Claude Code sessions running on a local machine. A local orchestrator must implement task selection, claim/lock handling, branch/worktree isolation, delegation, and status updates. Do not launch multiple coding agents against one working directory. Keep final merge authority with the repository owner.
