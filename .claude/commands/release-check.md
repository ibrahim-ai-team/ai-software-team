---
description: Check release readiness, evidence, risks, and required human approvals
---

# Release readiness check

Evaluate whether the requested release is ready for human approval. Delegate the evidence checklist and go/no-go recommendation to `release-manager` when available; the coordinator reconciles its report with repository and CI evidence. This command does not deploy or release software.

## Procedure

1. Identify the release scope, target environment, and required approvals.
2. Verify linked pull requests, required CI checks, test results, and known defects.
3. Ask `release-manager` to coordinate the readiness checklist, changelog/release notes, rollback triggers, and unresolved owner decisions. Ask `sre-observability-engineer` to report telemetry/runbook/recovery readiness and `performance-engineer` to report performance evidence when relevant. Ask `code-review-security` for a read-only review of the actual diff and evidence; use `release-management`, `observability-sre`, `security-threat-modelling`, and `git-github-workflows` skills where relevant.
4. Record each check as PASS, FAIL, BLOCKED, or NOT APPLICABLE with evidence.
5. List blockers and decisions required from the owner.
6. Use templates/release-readiness-template.md for the report.

Never infer a green CI run from configuration alone. Do not deploy, tag, publish, or merge as part of this check.
