# Sprint record

> One file per sprint, e.g. `docs/sprints/S2.md`. Rules: `workflows/sprint-governance.md`. Check with `python scripts/check_governance.py docs/sprints/*.md`. Write real dates and real issue numbers only; if GitHub has no sprint field, say so in Membership source.

## Sprint

- Sprint ID: S1
- Start: YYYY-MM-DD
- End: YYYY-MM-DD
- Status: Planned
- Goal: one measurable outcome, e.g. "a learner completes one reviewed 10-question quiz on a phone"
- Approved by: not approved
- Membership source: GitHub milestone `S1` | Project iteration field `Sprint` | this file only (GitHub sprint field not configured)
- Release criteria: see `## Release criteria` in the project state (IDs RC-n)
- Capacity (points): 0
- Sessions planned: number (see `standards/sprint-sizing.md`; one session in reserve)

## Committed issues

Priority comes from the Project priority field or `priority:` label, never from the title. Added by is `plan` for the approved plan or the scope-change ID. Status: Ready, In Progress, In Review, Blocked, Done, Not done, Cancelled. Done needs the merged PR and evidence that says `merged`.

| Issue | Title | Priority | Points | Added by | Status | PR | Evidence | Next |
|---|---|---|---|---|---|---|---|---|

## Dependencies, risks and acceptance

| Issue | Depends on | Risk | Acceptance check |
|---|---|---|---|

## Out of scope

Items considered and left in the product backlog, with the reason.

## Scope changes

Unplanned work enters only through an approved row here. Displaces names what leaves the sprint (or `nothing: within capacity`).

| ID | Date | Issue | Change | Reason | Displaces | Decision | Decided by |
|---|---|---|---|---|---|---|---|

## Issue creation log

Every issue created during the sprint (gate: `workflows/backlog-quality-gates.md#issue-creation-gate`). Result: `new`, `subtask of #n`, `duplicate of #n` or `rejected`; a duplicate or rejected proposal is not created (Issue `-`). Target: `backlog` or this sprint ID.

| Issue | Problem | Duplicate search | Result | Target | Why now |
|---|---|---|---|---|---|

## Sprint review

Fill at sprint end (`/sprint-review`), then set Status to Closed. Every committed issue is Done, Not done, Blocked or Cancelled; anything not Done has a disposition in Next.

- Goal met: yes | partial | no
- Evidence: links to merged PRs, CI runs and acceptance checks
- Completed:
- Not done (stays open, re-prioritized):
- Blocked:
- Cancelled:
- Release check: `/release-check` result or not run
