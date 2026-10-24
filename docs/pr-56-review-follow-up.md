# PR #56 review follow-up and rollout evidence

Related: [PR #56](https://github.com/ibrahim-ai-team/ai-software-team/pull/56), [master 55-gap tracker #66](https://github.com/ibrahim-ai-team/ai-software-team/issues/66), and the separate API Quiz follow-up [issue #117](https://github.com/ibrahim-ai-team/api-quiz-app/issues/117).

This document separates corrections made in this PR from evidence that requires live GitHub or Claude Code access. Offline tests are not represented as live integration proof.

## Review finding 1 — Traceability

- Tracking issue: [#66 — MASTER TRACKER](https://github.com/ibrahim-ai-team/ai-software-team/issues/66).
- API Quiz application change is tracked separately in [api-quiz-app #117](https://github.com/ibrahim-ai-team/api-quiz-app/issues/117).
- The PR body now references #66. The app issue does not close as part of this kit-only PR.

## Review finding 2 — Sprint approval authority

The authority model is:

1. The human sponsor approves the sprint unless a standing delegation is explicitly recorded in the project's committed state.
2. Under that recorded delegation, the Product Owner may approve only plans within the approved MVP scope, capacity, and release criteria.
3. A delegation must have a durable decision ID and be referenced in the sprint record's `Approved by` field with approver and date. A chat statement, agent assumption, or absence of objection is not approval.
4. If the delegation is missing, ambiguous, expired, or outside its scope, stop and request sponsor approval. Do not activate the sprint until approval is recorded.
5. The plan is reported to the sponsor in either case. Human final authority over merge remains unchanged.

## Review finding 3 — Existing sprint-record compatibility

The repository audit found the sprint template and simulated records in tests, but no committed `docs/sprints/*.md` operational sprint records at the time of this PR review. Therefore there are no known committed historical sprint records to migrate in this repository; this is not a claim about local or uncommitted files.

Before enabling enforcement in another checkout:

- Inventory sprint record files first.
- Run `python scripts/check_governance.py <record paths>` against each existing record.
- Preserve the original file/history and decisions; migrate a copy or use a dedicated PR.
- Add missing required fields (real dates, approval, membership source, capacity, committed issue table, scope-change and issue-creation logs, closure review).
- Re-run the checker and retain the before/after report. Never invent historical dates, approvals or GitHub membership. If evidence is absent, record the field as unknown and keep the record out of Active/Closed status until resolved.

## Review finding 4 — End-to-end workflow evidence

The existing Phase 9 governance tests are offline simulations. They exercise duplicate rejection, scope protection, Done evidence, sprint closure/replanning, release conflicts, and PR-body/merge-policy checks. They do **not** prove live Claude Code delegation, GitHub Project synchronization, or a real implementation-to-PR run.

Minimum supervised acceptance scenario:

1. Submit one small test idea and record the approved brief and acceptance criteria.
2. Verify the design decision: attach a real design artifact or a documented, approved exception before applicable frontend work.
3. Search for duplicates, create/link the backlog issue, and record priority, dependencies, AC and verification evidence.
4. Plan a two-week sprint with real dates, committed issue numbers, capacity and explicit approval.
5. Run one bounded implementation task on a branch, record tests, open a PR and keep the issue/PR links traceable.
6. Verify Project status is actually saved by reading the item back; if Project access is unavailable, mark this step BLOCKED rather than passed.
7. Review QA/CI evidence and demonstrate that the agent cannot merge or push to main; human retains final approval and merge.
8. Close the sprint only after every committed item has a disposition and evidence.

Record the tested commit SHA, issue/PR URLs, CI run URLs, Project read-back and runtime observations in the pilot issue. Until this live supervised run is completed, overall readiness remains **NO-GO for unattended execution**.

## Review finding 5 — Enforcement and security

Live Claude Code delegation/permissions and GitHub rulesets/branch protection were not verified in this PR. They remain explicit rollout gates tracked in [issue #62](https://github.com/ibrahim-ai-team/ai-software-team/issues/62). Do not claim they pass based on text files or offline tests. Verify effective settings and required checks with authorized access; if access is unavailable, document the exact manual verification required. Do not change org/repository security settings without explicit authorization.

## Review finding 6 — API Quiz release follow-up

The kit-only scope is preserved. The separate application work is tracked in [api-quiz-app issue #117](https://github.com/ibrahim-ai-team/api-quiz-app/issues/117): apply the approved 24-reviewed-question/3-topic MVP threshold, retain all content-quality checks, remove the deploy-time bypass, and treat 60/8 as future scope. This application issue must be implemented and reviewed separately; it is not complete because it has been created.

## Review finding 7 — PR-body validation

The PR body references tracking issue #66 and retains the required Sprint, Validation evidence, and human-merge statements. Run the PR-body checker against the final body before declaring this finding resolved.

## Evidence classification

| Area | Current evidence | Status |
|---|---|---|
| Offline governance rules/tests | Unit tests and static checks in CI | Simulated/static; not live integration |
| Historical sprint records | No committed operational records found in the audited repository snapshot | No known migration targets; re-inventory before enforcement |
| GitHub Project status synchronization | Workflow/documentation exists; live read-back not evidenced here | Unverified; see #58 |
| Claude Code runtime delegation | Not exercised in this PR | Unverified; see #62/#65 |
| Branch protection and required checks | Not verified with effective admin/ruleset access | Unverified; see #62 |
| API Quiz thresholds and deployment | Separate application issue #117 | Not fixed by this kit PR |
| Final readiness | Requires supervised live pilot and security verification | NO-GO for unattended use |

Do not mark this review fully resolved until the code/docs fixes are validated, and keep the live runtime/security gates explicitly open until evidence is attached.
