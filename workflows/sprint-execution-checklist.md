# Sprint execution checklist

A quick checklist; the rules themselves are in `workflows/sprint-governance.md`. Run `python scripts/check_governance.py <sprint records>` at each stage.

## Before sprint commitment

- [ ] Product Owner priority is explicit.
- [ ] Sprint record has its ID, real dates, one measurable goal, capacity and the sponsor approval.
- [ ] Committed issues are listed in the record (and in GitHub when a sprint field or milestone is configured).
- [ ] Selected stories are Ready and have acceptance criteria.
- [ ] Dependencies, risk, and external access are identified.
- [ ] QA, security, documentation, and delivery work are represented.
- [ ] Scope and non-goals are visible in durable project state.

## During the sprint

- [ ] Unplanned work enters only through an approved scope change that names what it displaces.
- [ ] Each new issue passed the issue creation gate and is in the issue creation log.

## Before implementation

- [ ] Reconcile branch, commit, working tree, state file, and active task ownership.
- [ ] Assign a stable task ID and one accountable owner.
- [ ] Record allowed paths, inputs, outputs, dependencies, and expected evidence.
- [ ] Avoid overlapping edits in shared working trees.

## Before marking a story Done

- [ ] Acceptance criteria verified against observable behavior.
- [ ] Relevant automated checks executed and results captured.
- [ ] Diff reviewed for secrets, permissions, regressions, and unintended scope.
- [ ] Documentation and handover updated where needed.
- [ ] PR/CI status checked when remote access is available.
- [ ] Unrun checks and known limitations stated explicitly.

## Sprint close

- [ ] Close on the end date; do not extend the sprint.
- [ ] Every committed issue is Done, Not done, Blocked or Cancelled; report the groups separately.
- [ ] Incomplete issues stay open with a disposition (backlog or candidate for the next sprint); nothing carries over without replanning.
- [ ] Capture evidence-based outcomes and risks.
- [ ] Update next actions and decisions needed.
- [ ] Do not mark the overall project Complete while scope or Definition of Done remains unverified.
