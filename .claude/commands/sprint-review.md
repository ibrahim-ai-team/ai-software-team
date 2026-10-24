---
description: Review sprint outcomes, acceptance feedback, and remaining risks
---

# Sprint review

Closes the sprint by its end date under `workflows/sprint-governance.md#sprint-closure`. Ask `qa-automation` for verification evidence and `project-manager` for delivery state; the coordinator reconciles them with GitHub (merged PRs, CI runs, issue state). Skills: `test-strategy-automation`, `agile-planning`.

## Inputs

- The sprint record (goal, committed issues, scope changes, issue creation log)
- Pull requests, CI results, test evidence and release artifacts
- Acceptance feedback and unresolved risks

## Procedure

1. Compare the outcome with the goal: `Goal met: yes | partial | no`, with evidence links.
2. Give every committed issue a final status (Done, Not done, Blocked, Cancelled). Done requires the merged PR and verified acceptance criteria; an open or approved PR is not Done.
3. For anything not Done, keep the issue open and record its disposition in Next (`backlog` or `candidate S<n+1>`, plus what must change).
4. Summarize demonstrated functionality, quality results, known defects and risks; run `/release-check` if a release is planned.
5. Record sponsor feedback and decisions without inventing approval; close story issues only when their acceptance is recorded.
6. Fill `## Sprint review` in the sprint record (and `templates/sprint-review-template.md` if a separate report is wanted), set `Status: Closed`, and run `python scripts/check_governance.py <sprint records>`.

Do not claim a feature is delivered, tested, or deployed without evidence. Do not extend the sprint. Do not merge pull requests.
