# GitHub Projects setup for the AI team

This is a manual setup guide. It does not create a GitHub Project or modify repository settings automatically.

## Recommended project fields

Create a GitHub Project linked to this repository and add:

- **Status:** Backlog, Ready, In Progress, In Review, Changes Requested, Approved — Awaiting Human Merge, Blocked, Done.
- **Priority:** P0, P1, P2, P3.
- **Iteration:** two-week sprint iterations.
- **Estimate:** a small effort scale such as 1, 2, 3, 5, 8; split work estimated above 5 where practical.
- **Work type:** Story, Bug, Tech Debt, Framework Proposal, Documentation, Infrastructure.
- **Owner:** responsible human or agent identity/label supported by your orchestration setup.
- **Dependencies:** use issue relationships or explicit links in the issue body.

GitHub Projects features and field availability can vary by project type and account permissions; configure equivalent fields if names differ.

## Canonical status and transition rules

The Project V2 single-select `Status` field is the source of truth for board status; issue titles must not carry status prefixes as a second source of truth. Use `workflows/project-status-transitions.md` for permitted transitions, event triggers, and required evidence. Use `workflows/backlog-quality-gates.md` for Definition of Ready and QA decomposition. A manual setup guide is not automation: verify the actual project fields, options, and item status after configuration.

## Recommended views

1. **Product Backlog:** Status is Backlog, sorted by priority.
2. **Current Sprint:** Iteration is the active two-week sprint; group by Status.
3. **Ready to Claim:** Status is Ready; show priority, estimate, dependencies, and owner.
4. **Review Queue:** Status is In Review or Changes Requested.
5. **Approved — Human Merge:** Status is Approved — Awaiting Human Merge.
6. **Blocked:** Status is Blocked, with blocker details visible.
7. **Sprint Review:** current iteration grouped by Done / unfinished work.

## Labels to add

Suggested issue labels: type:story, type:bug, type:tech-debt, type:framework-proposal, type:docs, priority:P0, priority:P1, priority:P2, priority:P3, status:blocked, needs:decision, needs:acceptance-criteria.

Labels do not enforce access control or prove an agent has claimed a task. Treat them as visible metadata.

## Sprint ceremony

- **Sprint planning:** choose a goal, confirm Ready items and dependencies, estimate capacity, and get human approval for the commitment.
- **During sprint:** keep status current, surface blockers quickly, and avoid adding major scope without explicit approval.
- **Sprint review:** show merged outcomes and evidence; list unfinished tasks honestly.
- **Retrospective:** record one or two actionable process improvements as backlog issues.

## Important limitations

GitHub Issues and Projects provide the board and durable task records, but they do not automatically coordinate Claude Code sessions running on a local machine. A local orchestrator must implement task selection, claim/lock handling, branch/worktree isolation, delegation, and status updates. Do not launch multiple coding agents against one working directory. Keep final merge authority with the repository owner.
