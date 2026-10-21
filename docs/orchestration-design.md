# Orchestration Design

This file is a short entry point; the operational contract is `workflows/orchestration-contract.md`.

## Single coordinator of record

The active top-level Claude Code session coordinates the project. The Project Manager role supplies planning and reporting responsibilities, but it is not a continuously running daemon and does not run when Claude Code is closed unless an external scheduler is separately configured.

## Activation and phases

A clear request to build an application idea starts discovery immediately. A request to inspect or improve this starter kit changes only this repository. Follow `workflows/project-bootstrap.md` for discovery, architecture, backlog preparation and material sponsor gates, then `workflows/agile-agent-delivery.md` for incremental delivery.

## Source of truth

Use actual repository/commit/PR/CI evidence for code facts; recorded sponsor decisions and ADRs for decisions; canonical task records for status; delegation/activity records for agent progress. Chat and agent statements are not proof. Reconcile records before daily reports and after each delegation.

## Concurrency and recovery

The current kit documents a safe single-writer protocol; it does not include a distributed lock service or a proven local orchestration runtime. Do not call markdown records or GitHub labels atomic locks. Parallel coding is allowed only with isolated branches/worktrees and non-overlapping ownership. Follow retry limits, stale-claim recovery, handover and failure classification in the orchestration contract.

## Safety and verification

The human owner alone merges PRs. Agents cannot enable auto-merge, push to the default branch, deploy production, or change permissions. These are documented policies, not enforced repository settings until rulesets/permissions are configured and verified. Static validation is not a runtime delegation test; use `docs/verification-report.md` to record actual Claude Code discovery and end-to-end verification.
