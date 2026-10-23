# Sprint governance

The single authority for sprint planning, scope protection, sprint closure, the next sprint and release criteria. Other files (commands, checklists, agents, templates) link here instead of restating these rules. Precedence between sources is in `workflows/orchestration-contract.md#authority-and-precedence`.

Record format: `templates/sprint-plan-template.md` (one file per sprint, e.g. `docs/sprints/S2.md`). Check: `python scripts/check_governance.py docs/sprints/*.md`. The checker reads the records only; it does not query GitHub, so the coordinator still compares the record with GitHub before reporting.

## Where sprint facts live

| Fact | Operational source | When it is not configured |
| --- | --- | --- |
| Sprint membership | GitHub milestone named after the Sprint ID, or the Project iteration field | The sprint record, with `Membership source: this file only`; say so in reports |
| Priority | Project priority field, else the `priority:` label | Never the issue title |
| Status | Project Status field (`workflows/project-status-transitions.md`) | Issue open/closed state plus the sprint record |
| Sprint ID, dates, goal, approval, capacity | The sprint record | Same |
| Scope changes, issue creation reasons | The sprint record | Same |
| Release criteria | `## Release criteria` in the project state | Same |

Never claim an issue belongs to a sprint, or that a sprint has dates, unless the record or GitHub shows it. A local, gitignored ledger is not project state; commit the sprint record to the project repository.

## Sprint planning

`project-manager` prepares the plan (`/plan-sprint`); `product-owner` sets priority; `tech-lead` provides points; the plan is approved as in item 7. A sprint has:

1. A unique ID `S1`, `S2`, ... in order.
2. Real start and end dates (default length two weeks). Sprints do not overlap.
3. One measurable goal.
4. Committed GitHub issues, each Ready (`workflows/backlog-quality-gates.md`), with points; total points within `Capacity (points)` (`standards/sprint-sizing.md`).
5. Dependencies, risks and the acceptance check per issue.
6. The Definition of Done (`standards/definition-of-done.md`) and the release criteria IDs that apply.
7. `Approved by` with the decision ID, approver and date. The approver is the sponsor, or the `product-owner` when the sponsor has recorded a standing delegation (a decision ID in the project state) for plans within the approved MVP scope, capacity and release criteria. This keeps the earlier rule that the sponsor is not asked to approve routine sprints (`docs/vision-alignment-audit.md` A3) while making every approval traceable. Only an approved sprint becomes Active; the plan is reported to the sponsor either way.

The next sprint starts on its planned start date after the previous sprint is Closed and the new plan is approved, not when an agent decides it is ready.

## Scope protection

After approval the committed list changes only through a row in `## Scope changes`:

- New ideas, optional features and agent proposals go to the product backlog (`Target: backlog`). They are not added to the current sprint.
- Urgent work (security incident, production defect, blocker for the sprint goal) enters with a scope change that names its reason, what it displaces, and an approving owner. The owner is the sponsor or, for work within the goal and capacity, the Product Owner.
- A re-estimate that pushes committed points over capacity is a scope change: split the story, displace work, or return it to the backlog.
- Every new issue passes the issue creation gate (`workflows/backlog-quality-gates.md#issue-creation-gate`) and is logged in `## Issue creation log`.
- Do not create issues to keep agents busy. When the sprint goal is blocked, work on the blocker, not on new features.

## Sprint closure

At the end date `/sprint-review` closes the sprint, whatever is unfinished:

1. Evaluate the goal: `Goal met: yes | partial | no`, with evidence links.
2. Verify acceptance criteria and the Definition of Done for each item; run the relevant tests and `/release-check` if a release is planned.
3. Give every committed issue a final status: Done (merged PR and evidence), Not done, Blocked or Cancelled. Report the four groups separately.
4. Keep incomplete issues open. Their `Next` says where they go: `backlog` or `candidate S<n+1>`, plus what must change (re-estimate, split, decision).
5. Close story issues only when their acceptance criteria are accepted; close an issue whose scope was cut only after the cut is recorded as a scope change or a new linked issue holds the remainder.
6. Set `Status: Closed`. A sprint is never extended because work remains; an Active sprint past its end date fails the check.

## Next sprint

Plan it from the backlog as a new sprint. Candidates from the previous sprint compete with the rest of the backlog on priority and capacity; nothing carries over automatically. A carried issue keeps its number and history.

## Release criteria

- One table in the project state holds each threshold with the decision that approved it. Code constants, planning documents and workflow defaults that repeat a value are listed as mirrors and must match it.
- When a newer human decision changes a criterion, update the table, record the old value in `## Requirement conflicts` until every mirror is updated, and ask the decision owner to confirm. Never choose the more ambitious or the more convenient value silently.
- A release passes only when `check_governance.py --state <state> --repo . --release` passes: mirrors agree, no conflict is open, and no workflow offers an input that skips the release criteria. Changing a threshold is a decision; overriding it at deploy time is not allowed.
