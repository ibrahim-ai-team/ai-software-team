# Agent Delegation Record

- **Delegation ID:** `TASK-<issue-id>-D<sequence>`
- **Task / Issue:** 
- **Agent role:** 
- **Task status:** BACKLOG / READY / CLAIMED / IN_PROGRESS / BLOCKED / IN_REVIEW / CHANGES_REQUESTED / APPROVED_AWAITING_HUMAN_MERGE / DONE / CANCELLED
- **Delegation result:** queued / running / completed / partial / blocked / failed / cancelled / rejected
- **Claim validation:** CONFIRMED / NEEDS_REVALIDATION
- **Claimed at (observed):**
- **Last checkpoint (observed):**
- **Branch / worktree:**
- **Allowed paths (exact directories/files):**
- **Size / points:** XS / S / M / L (1 / 2 / 3 / 5); XL (8) must be split
- **Turn cap (agent `maxTurns`):**
- **Estimated cost / measured cost (API-equivalent):**
- **Re-delegations after hitting the turn cap (max 1):**
- **Started at (observed):** 
- **Returned at (observed):** 

## Objective
What outcome is requested?

## Inputs and context
- Relevant requirements/decisions:
- Files, code, or links supplied:

## Expected output
- Deliverables:
- Acceptance checks:
- Dependencies:
- Exclusive file ownership / branch / worktree:

## Standard agent return (copy the fields below into the coordinator record)
- **Delegation ID:**
- **Delegation result:**
- **Changed paths:**
- **Commit / branch:**
- **Checks actually run and results:**
- **Evidence links:**
- **Risks / unresolved items:**
- **Observed token usage:** unavailable unless exposed by the runtime
- **Observed cost:** unavailable unless exposed by the runtime
- **Observed duration:**
- **Next recommendation:**

## Result reported by agent
Summarize only the actual response and artifacts returned. Do not treat an agent's claim as independent verification.

## Coordinator disposition
- **Disposition:** accepted / needs changes / partial / blocked / rejected / not yet reviewed
- **Files/commits/PRs inspected:**
- **Acceptance criteria checked:**
- **Evidence:** test output, CI run, commit, PR, document, or other observable artifact
- **Checks not run and why:**
- **Blocker or follow-up:**
- **Next action and owner:**

## Reconciliation checklist
- [ ] Status reflects the latest observed result.
- [ ] Artifacts and evidence are linked.
- [ ] Reported claims are distinguished from verified facts.
- [ ] Task/project status and handover are updated.
- [ ] No unsupported claim of completion, test success, merge, or deployment.
