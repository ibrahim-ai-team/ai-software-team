# Future Project Workflow

## Gate 0 — Project activation

This repository configures the reusable team only. When the user gives an application idea and asks the team to build it, treat that as activation of a future application project. Keep the application separate from this reusable team kit. If the user is only brainstorming or improving the team kit, do not create application code.

The active top-level Claude Code session is the coordinator of record. It is not a background daemon; work does not continue when Claude Code is closed unless an external scheduler/runner is configured. Follow `workflows/orchestration-contract.md` for state transitions, source-of-truth precedence, resumption, task ownership, recovery, evidence and reporting.

Follow `workflows/project-bootstrap.md` for discovery, specification, architecture/repository planning, safe setup, and delivery initialization.

## Gate 1 — Product discovery and specification

Product Owner and Business Analyst own product definition: clarify users, problem, goals, workflows, scope, constraints, risks, acceptance outcomes, and open questions. They should infer routine details responsibly and document assumptions. Ask the sponsor only for material unresolved decisions, not routine backlog management.

## Gate 2 — Architecture and delivery plan

Architect compares viable options against requirements and records consequential decisions as ADRs. Project Manager prepares the prioritized backlog, dependencies, delivery slices, and sprint plan. QA defines risk-based test strategy early. DevOps plans environments and CI/CD. Do not assume a framework, database, microservices, or multi-repository structure without a documented rationale.

## Gate 3 — Incremental implementation

Project Manager coordinates bounded work through the main Claude Code session. Each task needs one accountable owner, dependencies, allowed file paths, inputs, acceptance criteria and evidence. A markdown record or GitHub label is not an atomic lock. Do not run overlapping coding tasks in one shared working tree; parallelize only through isolated branches/worktrees and non-overlapping ownership. If no actual lock service exists, follow the single-coordinator/single-writer protocol.

The team may continue routine, reversible work within the agreed project direction. Do not spend money, change permissions, deploy to production, or perform destructive/irreversible actions without required human approval.

## Gate 4 — Verification

QA defines and executes available checks; developers report exact commands and results; Code Reviewer checks actual diffs and security risks. Keep implemented, tested, reviewed, merged, and deployed as distinct states. Never claim checks passed unless evidence exists. If runtime tools or CI are unavailable, state that limitation rather than implying success.

## Gate 5 — Project visibility and handover

Project Manager reconciles tasks, PRs, CI, blockers, risks, and pending decisions; updates durable records; publishes the daily report and handover. The sponsor can inspect the application's current state without reading every agent conversation. The human repository owner performs final PR merges. Repository rulesets/branch protection and permissions must be configured and verified separately; written policy alone does not enforce merge restrictions.

## Token and context management

- Work in bounded increments and prioritize high-risk unknowns.
- Reuse skills/templates instead of repeating long instructions.
- Delegate only independent tasks with explicit outputs and file ownership.
- Keep durable decisions in files and use concise handovers.
- On failure, preserve evidence, classify the cause and limit retries; do not repeat an unchanged failing attempt indefinitely.
- Pause only when required information, access, or approval is missing; state the exact reason and decision needed.
