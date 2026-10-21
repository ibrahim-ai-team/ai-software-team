---
description: Report project status from repository and durable state
---

# Status

Reconcile task and delegation state using `project-manager` guidance and `docs/agent-traceability.md`. Do not infer completion from agent claims; verify branch/PR/CI evidence. Use `documentation-session-handover` when updating durable state.

Reconcile current repository, project state, backlog/task records, branches, PRs, and CI where access exists. Report:

- Current phase and sprint goal
- Done/in progress/Ready/blocked stories with IDs and owners
- Latest commit, open PRs, and observed CI/test evidence
- Risks, dependencies, stale tasks, and sponsor decisions needed
- Next 1–3 actions

Distinguish verified facts from unverified notes. If a remote system is unavailable, say so and use local state; do not invent issue IDs, board updates, commits, or test results.
