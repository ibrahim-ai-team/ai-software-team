# AI Software Team — Project State

Last analysed: 2026-10-19
Repository: https://github.com/ibrahim-ai-team/ai-software-team
Default branch: `main`
Current phase: Supervised pilot readiness (team kit), no application work started

## Operating rules

- Work on feature branches and submit pull requests; never commit directly to `main`.
- The repository owner performs final merges.
- Separate static validation, offline/mock tests, live runtime tests, and production evidence. Never claim one proves another.
- Keep secrets, credentials, and private chain-of-thought out of this file and issue bodies.
- Use GitHub Issues as durable task records; update this file at meaningful session boundaries.

## Verified repository evidence (2026-10-19)

- Latest inspected `main` commit: `8bf343a` (merge of PR #44). CI on that commit: [Validate](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39077920728) and [Secret scanning](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39077920727) succeeded.
- PRs #29, #30, #31 and #44 are merged; #23 (durable state) is closed and this file is on `main`.
- Claude Code runtime discovery, one delegation and representative deny rules were observed in a cloud session: see [`docs/verification-report.md`](verification-report.md). A local CLI/Termux run and `ask`-rule prompting remain NOT VERIFIED.
- `main` protection (read back): PR required with 1 approval + code-owner review; force-push and deletion blocked; **no required status checks**; admins not enforced; no rulesets.
- GitHub MCP merge/auto-merge tools are not denied by `.claude/settings.json`.
- GitHub Project #1 fields, views and item statuses are not reachable from cloud sessions (GraphQL and org Project endpoints blocked); `project-status.yml` has never run. Board Status: NOT VERIFIED.

## Launch blockers for the first supervised pilot

| Order | Issue | Blocker | Owner of next action |
|---|---|---|---|
| 1 | [#24](https://github.com/ibrahim-ai-team/ai-software-team/issues/24) | Require PR + CI checks on `main`; close the MCP merge-tool gap | Repository owner (settings) and approved PR |
| 2 | [#25](https://github.com/ibrahim-ai-team/ai-software-team/issues/25) | Runtime evidence recorded; merge it and, if the pilot runs locally, repeat the smoke test there | Repository owner review |
| 3 | [#45](https://github.com/ibrahim-ai-team/ai-software-team/issues/45) | Run the first supervised pilot through discovery, backlog and the first reviewed PR | Coordinator, after 1–2 |

Everything else open (#26, #32, #34, #35, #36, #39, #40, #42, #43) can wait until after the pilot. Issue corrections were applied 2026-10-19; Project Status/view changes (not reachable from cloud sessions) are listed in [`docs/pilot-readiness.md`](pilot-readiness.md).

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
