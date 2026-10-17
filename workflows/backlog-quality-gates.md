# Backlog quality gates and mandatory QA decomposition

## Purpose
Every backlog item must be clear, prioritized, dependency-aware, and verifiable before it enters a sprint. QA participates during specification and refinement, not only after implementation.

## Roles
- Product Owner / Business Analyst: define user outcome, scope, assumptions, edge cases, and acceptance criteria.
- Project Manager: owns backlog completeness, task decomposition, dependencies, estimates, issue links, and readiness decision.
- QA Automation: independently reviews risk and acceptance criteria, maps each criterion to a verification method, and identifies distinct QA deliverables.
- Developer: proposes implementation-level tests and reports exact commands/results.
- Coordinator: reconciles actual issue/board state and records evidence; a role instruction is not proof of execution.

## Required flow
1. Create or update the parent story/bug/technical issue using the matching GitHub Issue Form.
2. Review every acceptance criterion for observable outcomes and failure states.
3. QA creates a criterion-to-test matrix with risk, test level, automation candidate, test data/environment, and evidence expected.
4. Decide per verification activity:
   - Include it in the implementation issue when the same owner can reasonably deliver and verify it within the same bounded change.
   - Create a separate linked QA issue when it is a distinct deliverable, has a separate owner/dependency, needs test infrastructure/data/environment, spans multiple stories, or is too large to verify within the parent issue.
   - Create a linked Bug issue for each confirmed defect that requires separate remediation; do not use a QA issue as a substitute for a bug.
5. Link issues using GitHub issue references and add a parent/child relation where supported. If parent/child issue types are unavailable, include reciprocal issue URLs in both bodies.
6. Set priority, estimate, owner, dependencies, expected evidence, and project fields when configured. Do not duplicate the board status in the title.
7. The Project Manager runs the Definition of Ready checklist before placing the item in Ready or selecting it for a sprint.
8. During implementation, report checks as PASS, FAIL, BLOCKED, or NOT RUN. Include command/job, environment/commit, timestamp when available, and artifact/log links. Never claim PASS from a plan, mock, code review, or unexecuted test.
9. When tests fail, determine whether it is a product defect, test defect, environment problem, or flaky test. File and link a Bug issue when a confirmed product defect needs separate work. Record flaky/environment issues transparently.
10. At sprint review, reconcile planned QA work, executed coverage, untested risks, linked bugs, and residual risks.

## Definition of Ready
A task cannot move to Ready until all applicable items are true:
- [ ] Clear outcome and bounded scope.
- [ ] Acceptance criteria are testable; relevant negative/error/boundary cases are considered.
- [ ] Priority is set in the issue and, when configured, on the Project board.
- [ ] Estimate is set or explicitly marked TBD with a refinement task/deadline; do not silently treat TBD as estimated.
- [ ] Dependencies and related issues are listed, or explicitly None.
- [ ] QA mapped each acceptance criterion to a verification method or documented why it is not applicable.
- [ ] Required distinct QA issues are created and linked, or the decision to keep tests in the parent issue is recorded with rationale.
- [ ] Test data, environment, isolation/cleanup, and evidence needs are known or tracked as dependencies.
- [ ] Security, privacy, accessibility, performance and reliability checks are considered proportionately to risk.
- [ ] Definition of Done and exit criteria are explicit.
- [ ] Owner and allowed scope are clear.

If a required field or ticket is missing, keep the task in Backlog and create a refinement follow-up. Do not invent evidence or create duplicate QA issues when suitable linked work already exists.

## Minimum verification evidence
For each completed check record:
- issue/acceptance criterion and test ID;
- exact command, test suite, or CI job;
- branch/commit and environment;
- result: PASS / FAIL / BLOCKED / NOT RUN;
- sanitized log/report/artifact link;
- failure classification and linked bug/follow-up where relevant.
