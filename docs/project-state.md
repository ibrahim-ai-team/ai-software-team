# AI Software Team — Project State

Last analysed: 2026-10-17
Repository: https://github.com/ibrahim-ai-team/ai-software-team
Default branch: `main`
Current phase: Infrastructure hardening and supervised pilot readiness

## Operating rules

- Work on feature branches and submit pull requests; never commit directly to `main`.
- The repository owner performs final merges.
- Separate static validation, offline/mock tests, live runtime tests, and production evidence. Never claim one proves another.
- Keep secrets, credentials, and private chain-of-thought out of this file and issue bodies.
- Use GitHub Issues as durable task records; update this file at meaningful session boundaries.

## Verified repository evidence

- Latest inspected main commit: `f2fa3576ed61b50c5393303723a0eb5876abdc6c` (includes merged PR #30).
- [Validation workflow run](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39076389223): success on the inspected revision.
- [Secret scanning workflow run](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39076389175): success on the inspected revision.
- [PR #30](https://github.com/ibrahim-ai-team/ai-software-team/pull/30): merged; adds a reusable per-application GitHub Project blueprint and updates the setup guide.
- `docs/project-state.md` was absent from `main` during the 2026-10-17 audit; this document is proposed on a feature branch and is not canonical on `main` until merged.
- GitHub API reported `main` as protected, but detailed protection rules could not be retrieved by the available integration. Exact review/check/force-push/deletion settings: **NOT VERIFIED**.
- Real Claude Code agent discovery, delegation, and permission enforcement: **NOT VERIFIED**.
- Real GitHub Project status update and read-back: **NOT VERIFIED**.
- Actual Project board fields/views have not been runtime-verified by this repository audit.

## Active work and next actions

| Issue | Purpose | Current assessment | Next action |
|---|---|---|---|
| [#23 — Durable project state](https://github.com/ibrahim-ai-team/ai-software-team/issues/23) | Canonical state and session handover | IN PROGRESS; this file is proposed on a branch | Review and merge the PR, then verify this file exists on `main`; only then close the issue |
| [#24 — Security and branch protection](https://github.com/ibrahim-ai-team/ai-software-team/issues/24) | Verify security guardrails and GitHub branch rules | NOT VERIFIED | Inspect actual GitHub rules and run safe permission checks; attach evidence |
| [#25 — Claude Code smoke test](https://github.com/ibrahim-ai-team/ai-software-team/issues/25) | Verify discovery, delegation and permissions in a real runtime | IN PROGRESS / NOT VERIFIED | Run controlled tests in an isolated throwaway clone using fake data; record results in `docs/verification-report.md` |
| [#26 — Sprint sizing and model routing](https://github.com/ibrahim-ai-team/ai-software-team/issues/26) | Define task budgets and routing based on supported runtime controls | BLOCKED pending runtime evidence | Resume after #25 documents actual installed-runtime capabilities |
| [#30 — Per-application Project blueprint](https://github.com/ibrahim-ai-team/ai-software-team/pull/30) | Reusable board setup guidance | MERGED | No board was created by this PR; configure boards manually when an actual application is initialized |

Always re-fetch issue/PR status before acting; the table is a dated snapshot, not a live status feed.

## Known workflow limitations

- `.github/workflows/project-status.yml` is manually triggered and targets organization Project #1 (infrastructure board) only.
- The current status workflow only searches the first 100 Project items.
- The workflow has not been proven by a successful real status update and read-back.
- Do not use the infrastructure Project status workflow for application Projects without parameterization, pagination, and safe testing.
- GitHub Projects does not coordinate local Claude Code sessions by itself. A future orchestrator needs task claim/lock handling, isolated branches/worktrees, evidence collection, and safe status updates.
- Static CI success does not prove live Claude Code permission enforcement.

## Session-resume checklist

1. Read this file and re-check linked issues, pull requests, and recent workflow runs on GitHub.
2. Confirm the current `main` SHA and whether this file is merged.
3. Inspect the relevant issue and branch before editing; do not assume this snapshot is current.
4. Select the highest-priority unblocked task whose dependencies are satisfied.
5. Create/use a feature branch; never work directly on `main`.
6. Make a bounded change, run relevant checks, and record exact commands/results and limitations.
7. Open a PR with evidence and a clear test summary. Do not merge; the human owner decides.
8. Update issue state and this file only when the corresponding evidence exists.

## Status vocabulary

- **IMPLEMENTED**: files/configuration exist.
- **STATIC-VALIDATED**: repository/static checks passed.
- **TESTED**: named tests were actually run and passed.
- **REVIEWED**: a review of the current revision was completed.
- **MERGED**: the change is on the target branch.
- **RUNTIME-VERIFIED**: behavior was observed in the actual target runtime/environment.
- **NOT VERIFIED**: evidence is absent, inaccessible, or insufficient.
