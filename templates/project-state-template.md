# Project State

> Keep this file free of secrets, tokens, personal data not needed for delivery, and private reasoning. Update from verified evidence.

## Snapshot

- Project ID/name:
- Last reconciled at (UTC):
- Current phase: DISCOVERY
- Goal and in-scope outcomes:
- Last known commit / branch:
- Current sprint (ID, dates, goal, record file):

## Product goal and approved MVP scope

- Product goal:
- MVP scope (stories in / out):
- Approved by (decision ID):

## Release criteria

The single place for release thresholds (`workflows/sprint-governance.md#release-criteria`). Mirrors lists every file that repeats a value, as `path: text with {value}`, separated by `;`. `python scripts/check_governance.py --state <this file> --repo . --release` fails if a mirror disagrees or a conflict is open.

| ID | Criterion | Value | Decision | Mirrors |
|---|---|---|---|---|

## Requirement conflicts

Record a conflict instead of picking one side (`workflows/orchestration-contract.md#authority-and-precedence`). Status: open or resolved.

| ID | Criterion | Sources | Status | Decision needed |
|---|---|---|---|---|

## Approved decisions

| ID | Decision | Owner/date | Evidence or ADR |
|---|---|---|---|

## Assumptions and open questions

| Item | Type | Impact | Owner | Next action |
|---|---|---|---|---|

## Backlog and task ownership

| Task ID | Status | Priority | Owner | Dependencies | Acceptance/evidence |
|---|---|---|---|---|---|

Allowed statuses: Draft, Ready, In Progress, Blocked, In Review, Done, Cancelled. Use Done only after acceptance criteria and verification evidence are checked.

## Active delegations

| Delegation ID | Task ID | Owner | Branch/worktree | Scope/allowed paths | Expected output | Status | run_id | session_id | Evidence |
|---|---|---|---|---|---|---|---|---|---|

Before dispatching, run `python scripts/check_claims.py <this file>`; it rejects two active claims on the same task, branch/worktree or overlapping paths.

## Pull requests and verification

| PR | Purpose | CI/test evidence | Review status | Next action |
|---|---|---|---|---|

## Risks and blockers

| Risk/blocker | Impact | Mitigation or required decision | Owner |
|---|---|---|---|

## Sponsor decisions needed

- Decision:
- Options/trade-offs:
- Recommendation:
- What can proceed safely meanwhile:

## Next actions

1.
2.
3.

## Change log

| UTC timestamp | Previous phase | New phase | Reason | Evidence |
|---|---|---|---|---|
