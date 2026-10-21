---
name: release-management
description: Use when preparing a release plan, version, changelog, go/no-go recommendation, rollback plan, or post-release verification.
---

# Coordinate evidence-based releases

## When to use

Use when a set of changes is being considered for release, a release candidate needs readiness review, or release notes and rollback steps must be prepared.

## Procedure

1. Confirm release scope, target environment, versioning policy, window, owners, and approval requirements.
2. Reconcile included PRs/commits, CI status, test evidence, security review, known defects, migrations, configuration, and compatibility.
3. Request missing evidence from the relevant owner; do not infer a pass from configuration or a claim.
4. Check monitoring/alerts, support/runbook readiness, backup/rollback path, and post-release verification criteria.
5. Draft a concise changelog/release note from verified changes; mark uncertain or unreleased items.
6. Record each checklist item PASS, FAIL, BLOCKED, or NOT APPLICABLE with evidence/rationale.
7. Provide a go/no-go recommendation and unresolved decisions to the human owner. Do not merge, tag, publish, or deploy unless explicitly authorized.

## Expected outputs

- Evidence-linked release-readiness checklist
- Version/changelog/release-note draft where requested
- Go/no-go recommendation, blockers, rollback triggers, and post-release checks

## Quality checks

- Merged, published, deployed, and deployment-verified are separate states.
- Every critical check has evidence or an explicit blocker/NOT APPLICABLE rationale.
- Human release authority and all unresolved risks are visible.
- Never report release success without observed evidence.
