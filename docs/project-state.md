# AI Software Team — Project State

Last analysed: 2026-10-19
Repository: <https://github.com/ibrahim-ai-team/ai-software-team>
Default branch: `main`
Current phase: Ready for the first supervised pilot (team kit); no application work started

## Operating rules

- Work on feature branches and submit pull requests; never commit directly to `main`.
- The repository owner performs final merges.
- Separate static validation, offline/mock tests, live runtime tests, and production evidence. Never claim one proves another.
- Keep secrets, credentials, and private chain-of-thought out of this file and issue bodies.
- Use GitHub Issues as durable task records; update this file at meaningful session boundaries.

## Verified repository evidence (2026-10-19, end of session)

- `main` at `2b388aa` (merge of PR #48). Merged today: #46 (readiness evidence), #47 (MCP merge-tool denial), #48 (backlog items).
- Closed today: #25 (runtime smoke test) and #32, #34, #35, #39, #40, #42, #43 (via #48).
- Runtime evidence (cloud session, Claude Code 2.1.303): discovery, delegation, deny rules and MCP merge-tool denial observed — [`docs/verification-report.md`](verification-report.md). Local CLI/Termux run and `ask`-rule prompting: NOT VERIFIED.
- `main` protection (read back): PR required with 1 approval + code-owner review; force-push and deletion blocked; **no required status checks**; admins not enforced; no rulesets.
- GitHub secret scanning, push protection and Dependabot security updates: **disabled** (owner settings; see `docs/security-and-governance.md`).
- Project #1 Status is updated and read back through `.github/workflows/project-status.yml` (verified runs in the verification report). Cloud sessions cannot reach Projects directly; use the workflow.

## Vision alignment (2026-10-19)

- Team model: `agile-orchestrator` is the single entry point and the only agent that can delegate; `tech-lead` added; 18 agents. Gap analysis: [`docs/vision-alignment-audit.md`](vision-alignment-audit.md).
- `main` protection read back: PR required, 0 approvals, 4 required checks, no bypass, force-push and deletion blocked (#24 closed).
- Live runs RT-13 to RT-18 in [`docs/verification-report.md`](verification-report.md): delegation from idea to task breakdown, and resume from this file.

## Open work

| Issue | Status on board | Next action | Owner |
| --- | --- | --- | --- |
| [#45](https://github.com/ibrahim-ai-team/ai-software-team/issues/45) | Ready | Start with `claude --agent agile-orchestrator` once the owner gives an idea | Owner input, then `agile-orchestrator` |
| [#26](https://github.com/ibrahim-ai-team/ai-software-team/issues/26) | Backlog | Calibrate sizing/budgets from pilot data | After #45 |

Board housekeeping still owner-only: #25 shows `In Progress` although closed (the Done gate needs a PR saying `Closes #25`; drag it or enable the Project's "Item closed → Done" workflow); enable "Auto-add to project" so new issues land on the board.

Always re-fetch issue/PR status before acting; the table is a dated snapshot, not a live status feed.

## Known workflow limitations

- `.github/workflows/project-status.yml` updates one issue per run; GitHub keeps one pending run per issue, so wait for each step before dispatching the next transition for the same issue.
- Use it for application Projects only after copying it into the application repository and testing it there.
- Claims are coordination records checked by `scripts/check_claims.py`, not locks; parallel coding needs separate worktrees/branches.
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
