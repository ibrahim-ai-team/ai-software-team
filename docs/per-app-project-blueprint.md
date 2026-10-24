# Reusable GitHub Project blueprint for each application

## Purpose and boundaries

Use one GitHub Project per real application. Keep the existing organization Project #1 for the AI team infrastructure repository; do not turn it into an application board and do not create a second infrastructure board.

A product repository may contain a backend, frontend, mobile client, and tests. They can share one application Project when they are parts of the same product and release goal. Create separate Projects only when teams/releases genuinely need separate planning.

This document is a configuration blueprint. It does not create a Project or change organization settings by itself.

## Required fields

Configure these fields on each application Project. If a field already exists, reuse it; do not create a duplicate with a slightly different name.

| Field | Type | Options / convention | Purpose |
| --- | --- | --- | --- |
| Status | Single select | Backlog, Ready, In Progress, In Review, Changes Requested, Approved — Awaiting Human Merge, Blocked, Done | Canonical workflow state |
| Priority | Single select | P0, P1, P2, P3 | Ordering and escalation |
| Iteration | Iteration field | Two-week iterations | Sprint membership |
| Estimate | Number or single select | 1, 2, 3, 5, 8 | Relative effort; split work above 5 where practical |
| Work type | Single select | Story, Bug, Tech Debt, Framework Proposal, Documentation, Infrastructure, QA | Classification |
| Owner | Assignee or single select | Real GitHub assignee where possible; otherwise named role | Accountability |
| Evidence / PR | URL or text | Issue, PR, CI, test-report URL | Traceability |
| Dependencies | Text or issue relationships | Link blocked-by / depends-on issues | Expose sequencing constraints |

Keep the Project's built-in item title and issue body for descriptions, not status. Never infer status from title prefixes. Use the exact status transition contract in `workflows/project-status-transitions.md`.

## Required views

Create these views in order. All views should use the same Project and source fields; views are saved filters, not separate backlogs.

1. **Product Backlog** — table view; include all unfinished product work, including Backlog and Ready. Exclude Done. Sort by Priority (P0 first), then Estimate. This is the complete pool of work not yet completed.
2. **Sprint actif** — board grouped by Status; filter Iteration = current iteration and Status != Done. Show Status, Priority, Estimate, Owner, Work type, and Dependencies. This contains only work committed to the current sprint.
3. **Sprint prochain** — table view; filter Iteration = next iteration and Status in Backlog or Ready. These are candidates, not a commitment. At sprint planning, re-check readiness, dependencies, capacity, and sprint goal before committing.
4. **Ready to Claim** — table or board; filter Status = Ready and no active owner/claim. Show Priority, Estimate, Dependencies, Work type, and Owner. A board filter alone does not provide a safe agent lock.
5. **QA & Review** — board grouped by Status; filter Status = In Review or Changes Requested or Approved — Awaiting Human Merge. Include PR/evidence and test result links.
6. **Blocked** — table or board; filter Status = Blocked. Keep blocker, needed decision/owner, impact, and next action visible in the issue body.
7. **Sprint Review** — table; filter Iteration = current iteration. Group or sort by Status and show Done versus unfinished work. Only report Done after the agreed Definition of Done is verified.

If the GitHub Project UI does not support a filter exactly as written, use the closest supported filter and record the deviation in the app's README or project setup notes. Do not silently pretend a view is filtering correctly.

## Planning rules

- **Product Backlog** = all known unfinished work.
- **Sprint prochain** = candidate work for the next two-week sprint; not yet committed.
- **Sprint actif** = work explicitly committed to the current sprint after planning.
- Do not put every backlog issue into an iteration. Assign an iteration only when it is selected for a sprint or deliberately prepared as a next-sprint candidate.
- The Product Owner / Business Analyst clarifies outcomes and acceptance criteria. QA maps tests to acceptance criteria and creates separate QA issues when testing is a distinct deliverable.
- The Project Manager proposes priority, dependencies, estimates, and sprint scope. The human owner approves the sprint commitment and retains final PR merge authority.
- Use small deliverable issues, ideally estimate 1–5. Split items estimated 8 where practical. Do not start blocked or unready work.
- During a sprint, new urgent work requires an explicit scope decision; document what is added and what is deferred.
- At sprint review, show merged outcomes and test evidence; carry unfinished work forward explicitly rather than counting it as Done.
- At retrospective, create one or two actionable improvement issues instead of leaving lessons only in chat.

## Bootstrap checklist for a new application

- [ ] Confirm the application repository/repositories and the person responsible for the product.
- [ ] Check the organization for an existing Project for this application; reuse it if it already exists.
- [ ] Create one organization Project linked to the relevant application repository/repositories.
- [ ] Add the required fields and exact Status options above, reusing existing compatible fields.
- [ ] Create the seven views above and verify each view's filter with representative issues.
- [ ] Add the issue forms and labels from the shared infrastructure where appropriate.
- [ ] Add initial discovery/specification/architecture/QA tasks to Product Backlog; do not invent a framework before discovery.
- [ ] Create the first two-week iteration only after the team has a realistic sprint goal and capacity.
- [ ] Verify Project access and any token permissions separately. Do not store tokens in files or issue bodies.
- [ ] Record the Project URL, field names, deviations, and owner in the application README or docs.

## Automation and safety

Project creation and view configuration are not performed by this document. Until an authorized bootstrap tool is implemented and tested, create/configure Projects in GitHub's UI and verify the result manually.

Project V2 board status synchronization is manual by design. For each application board, update the Status field directly in GitHub Projects and read it back. Do not copy or promise an unverified automation workflow, and never grant broader permissions merely to make an automation pass.

GitHub Projects does not coordinate local Claude Code sessions on its own. A future orchestrator must add claim/lock handling, isolated branches or worktrees, evidence collection, and safe status updates. Do not run multiple coding agents in one shared working directory. Never merge a PR automatically.
