---
name: agile-planning
description: Use when sequencing work, planning a sprint, or managing delivery dependencies.
---

# Plan small, reviewable increments

## When to use

Use this skill before selecting sprint scope, splitting work, sequencing dependencies, or resolving a delivery blocker.

## Required inputs

The project state (goal, MVP scope, release criteria, open conflicts), the previous sprint record, the prioritized backlog with Project fields, and `tech-lead` points. If a required input is missing, stop and ask the orchestrator for it instead of assuming it.

## Procedure

Clarify the goal, capacity, dependencies, risks, and acceptance checks. Break work into sprint-sized slices with clear ownership. Default to a two-week sprint. Size tasks and fit capacity to the sessions planned with `standards/sprint-sizing.md` (subscription usage, no dollar budgets). Track blockers and scope changes. Follow `workflows/sprint-governance.md` for the sprint record, approval, scope changes and closure; ask the sponsor directly only when the plan changes agreed scope, cost, risk, release criteria or a deadline, or no standing delegation is recorded.

## Expected outputs

- Sprint goal and bounded scope, with explicit exclusions
- Ordered tasks with owners, dependencies, acceptance checks, and WIP assumptions
- Blockers, risks, capacity assumptions, and next actions

## Quality checks

- Reject work without testable acceptance checks or a named owner.
- Keep WIP explicit; default to one implementation delegation per shared working tree.
- Record scope changes and decisions rather than silently expanding the sprint.
