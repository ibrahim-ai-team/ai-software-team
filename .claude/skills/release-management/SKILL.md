---
name: release-management
description: Coordinates evidence-based releases and prepares the human go/no-go decision. Use when preparing a release plan, version, changelog, rollback plan or post-release verification.
---

# Coordinate evidence-based releases

## When to use

Use when a set of changes is being considered for release, a release candidate needs readiness review, or release notes and rollback steps must be prepared.

## Required inputs

The release scope (PRs/commits), the release criteria table and decision IDs from the project state, CI and QA evidence, known defects, and the rollback path.
## Procedure

1. Confirm release scope, target environment, versioning policy, window, owners, and approval requirements.
2. Read the release criteria from the project state (one table, with decision IDs) and run `python scripts/check_governance.py --state <state> --repo . --release`. A mismatched mirror, an open requirement conflict or a release-override input is a blocker for the sponsor, not something to work around.
3. Reconcile included PRs/commits, CI status, test evidence, security review, known defects, migrations, configuration, and compatibility.
4. Request missing evidence from the relevant owner; do not infer a pass from configuration or a claim.
5. Check monitoring/alerts, support/runbook readiness, backup/rollback path, and post-release verification criteria.
6. Draft a concise changelog/release note from verified changes; mark uncertain or unreleased items.
7. Record each checklist item PASS, FAIL, BLOCKED, or NOT APPLICABLE with evidence/rationale.
8. Provide a go/no-go recommendation and unresolved decisions to the human owner. Do not merge, tag, publish, or deploy unless explicitly authorized.

## Expected outputs

- Evidence-linked release-readiness checklist
- Version/changelog/release-note draft where requested
- Go/no-go recommendation, blockers, rollback triggers, and post-release checks

## Quality checks

- Merged, published, deployed, and deployment-verified are separate states.
- Every critical check has evidence or an explicit blocker/NOT APPLICABLE rationale.
- Human release authority and all unresolved risks are visible.
- Never report release success without observed evidence.
- No release passes through an override of its own criteria; a threshold changes only by a recorded human decision.
