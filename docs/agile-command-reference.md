# Agile command reference

The commands under .claude/commands/ are reusable session prompts, not a background service. They run only when invoked in a Claude Code session. Availability and invocation syntax can vary by installed Claude Code version; verify commands are discovered in the actual runtime.

## Suggested flow

1. /kickoff — discover the idea, capture assumptions, and identify material decisions.
2. Follow workflows/project-bootstrap.md to produce requirements and architecture decisions.
2a. /provision-project — after sponsor approval of the plan, create the idea's repositories, issues and board idempotently (docs/project-provisioning.md).
3. /plan-sprint — select a small set of Ready stories with testable acceptance criteria.
4. /next-story — take one dependency-ready task and work within its bounded scope.
5. /review-pr — inspect the real diff and evidence before requesting merge.
6. /status and /daily-report — reconcile progress from durable state and observable evidence.
7. /sprint-review — compare sprint outcomes with the goal and record stakeholder feedback.
8. /retro — select a small number of measurable process improvements.
9. /release-check — assess release readiness; this command does not deploy.
10. /handover — preserve a resumable state before ending the session.
11. /approve-gate — use when a material sponsor decision is genuinely required.

## Operating rules

- Treat repository contents, commit/PR state, and observed CI results as evidence; chat history and agent claims are not proof.
- Every task needs a stable ID, one accountable owner, dependencies, allowed scope, acceptance criteria, and evidence.
- Use single-writer coordination in a shared worktree. Parallel coding needs isolated worktrees/branches and non-overlapping ownership; markdown status is not an atomic lock.
- The human repository owner makes the final merge decision. Commands must not merge PRs.
- Do not claim GitHub Issues, Projects, CI, deployment, or tests were updated/run unless verified.
- Stop at material gates for spending, production deployment, destructive actions, security/privacy risk acceptance, or unclear repository access.
- The team does not run while Claude Code is closed unless a separate scheduler/runner is configured.

See workflows/orchestration-contract.md for phase transitions, recovery, source-of-truth precedence, and reporting requirements.
