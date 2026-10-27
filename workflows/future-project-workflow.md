# Future Project Workflow

Entry point for building an application with this team. Each rule lives in the file linked below.

## Gate 0 — Project activation

This repository configures the reusable team only. When the user gives an application idea and asks the team to build it, that activates a future application project, kept separate from this kit. If the user is only brainstorming or improving the team kit, do not create application code.

The active top-level Claude Code session is the coordinator of record. It is not a background daemon: work stops when Claude Code is closed unless an external scheduler is configured.

## Where each stage is defined

| Stage | Defined in |
| --- | --- |
| Phases, state, resume, ownership, recovery, evidence, sponsor boundaries | `workflows/orchestration-contract.md` |
| Discovery, specification, architecture and repository planning, setup | `workflows/project-bootstrap.md` |
| Implementation, gates, verification, PRs, daily loop | `workflows/agile-agent-delivery.md` |
| Sprint planning, scope, closure, release criteria | `workflows/sprint-governance.md` |
| Backlog readiness and QA decomposition | `workflows/backlog-quality-gates.md` |
| UI design handoff before frontend work | `workflows/design-gate.md` |
| Usage limits, sizing and token-saving practices | `standards/sprint-sizing.md` |

## Invariants

- The team infers routine details, documents assumptions and keeps going; the sponsor is asked only for material decisions.
- A markdown record or GitHub label is not an atomic lock. Never run overlapping coding tasks in one working tree; parallelize only through isolated branches/worktrees with non-overlapping ownership.
- Never spend money, change permissions, deploy to production or take destructive actions without the required human approval.
- Implemented, tested, reviewed, merged and deployed are distinct states; never claim a check passed without evidence.
- The human repository owner performs final merges. Rulesets, branch protection and permissions must be verified separately; written policy alone does not enforce them.
