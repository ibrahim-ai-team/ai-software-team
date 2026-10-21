---
description: Produce a concise daily delivery report from reconciled evidence
---

# Daily report

Use `project-manager` operating rules and `documentation-session-handover`. Report only observed evidence; separate implemented, tested, reviewed, merged, deployed, and not verified.

Reconcile durable project state with actual repository, task, PR, and CI evidence where available. Report:

- Sprint goal and current phase
- Completed work with links/IDs and evidence
- Work in progress and next action per item
- Test/CI results, naming checks actually run
- Blockers, risks, dependencies, and sponsor decisions
- Scope or plan changes since the last report

Run this at the end of every session as the Project Manager report, and save it with `/handover` (completed work, Issue and PR links, validation results, blockers, next steps). Include sessions and delegations used and any usage-limit warning; never dollar costs.

Use concise language. Do not count unverified claims as completed work, invent remote updates, or report checks as passed unless they were run and observed.
