# Example Walkthrough: From Idea to Reviewed Delivery

This is an illustrative example for learning the workflow. It is not a record of a real Claude Code run, a real application, or verified runtime behavior.

## Example idea

> Build a small website where people can browse public library events and save events to a personal list.

## 1. Discovery and requirements

Invoke `/kickoff` in Claude Code from this repository and provide the idea. The coordinator should capture:

- Target users and outcomes
- In-scope and out-of-scope behavior
- Questions and assumptions
- Accessibility, privacy, reliability and performance needs
- Acceptance criteria and risks

**Illustrative output:** visitors can browse events by date, filter by category, view event details, and save an event after signing in. Sending invitations and taking payments are out of scope.

Do not begin application implementation during framework discovery unless the owner explicitly starts that project.

## 2. Architecture and decisions

Ask the architecture role to compare suitable options against the actual requirements. Record material choices as ADRs, including alternatives and consequences. Select front-end, back-end, persistence, testing tools and deployment approach from the requirements rather than assuming a stack in advance.

If authentication, personal data, external integrations, uploads, or privileged operations are in scope, complete the threat-model checkpoint in `workflows/orchestration-contract.md`.

## 3. Backlog and readiness

Use `/plan-sprint` to propose a two-week sprint goal and prioritized stories. Each story should include:

- User value and acceptance criteria
- Dependencies and estimate
- QA coverage and test data needs
- Security and accessibility checks where relevant
- Definition of Done and evidence expected

Example story: “As a visitor, I can filter events by date so that I can find an event that fits my schedule.”

Do not commit the sprint until capacity and dependencies are checked. Create GitHub Issues only when the repository/project owner has authorized the target board and issue creation.

## 4. Bounded implementation

Use `/next-story` to select one Ready task. Assign one accountable owner, a branch/worktree, allowed paths, input commit, and acceptance checks. Avoid multiple writers in the same working directory. Keep implementation incremental and open a pull request for review.

## 5. QA and review

Run the relevant unit, integration, API, UI, accessibility and security checks based on the chosen architecture. Record actual commands, outcomes, skipped checks, and environment limitations. Use `/review-pr` for a separate review; a reviewer must not claim tests passed when they were not run.

A PR being opened or approved is not the same as being merged or delivered.

## 6. Human merge and release readiness

The human repository owner makes the final merge decision. After merge, reconcile the issue, PR, CI results, acceptance evidence and project board. Use `/release-check` to review release readiness, outstanding risks, rollback, monitoring, and documentation.

Only mark a task Done when the configured Definition of Done is satisfied and the human merge is verified.

## Example traceability chain

`Idea → requirements → ADR → GitHub Issue/story → branch → PR → checks/review → human merge → reconciled status`

This walkthrough is a teaching example. Real status changes, CI results, runtime discovery and security enforcement must be evidenced separately.
