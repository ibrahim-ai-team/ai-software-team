---
name: observability-sre
description: Designs observable, reliable services with SLOs, telemetry, actionable alerts and runbooks. Use when defining reliability objectives, alerting, incident response or production-readiness checks.
disable-model-invocation: true
---

# Design observable and reliable services

## When to use

Use when a service needs operational readiness, diagnosability, reliability targets, failure handling, alerting, or recovery procedures.

## Required inputs

The service's user journeys, the reliability objectives or the decision that none apply, the current telemetry and alerting, and the deployment model.

## Procedure

1. Identify critical user journeys, dependencies, failure modes, data sensitivity, and operational owners.
2. Propose measurable SLIs and SLOs only when requirements and measurement windows can be stated; document assumptions.
3. Specify structured logs, metrics, traces, correlation identifiers, and dashboards that answer actionable operational questions.
4. Define alerts with symptom, threshold rationale, severity, owner, runbook, and response action; avoid noisy alerts.
5. Review timeouts, bounded retries, health/readiness checks, graceful degradation, and dependency failure behavior.
6. Document incident triage, recovery, rollback, backup/restore, and post-incident follow-up where applicable.
7. Separate config/code review from live-environment verification; link evidence or mark it unavailable.

## Expected outputs

- SLI/SLO proposal and assumptions
- Telemetry/dashboard/alert specification or bounded implementation
- Runbook, failure-mode and recovery notes, operational readiness checklist

## Quality checks

- Never log secrets or unnecessary personal data; define retention/access considerations.
- Every recommended alert has a response owner and action.
- Verify telemetry in the target environment before calling it operational.
- Never invent uptime, incident history, measured SLO compliance, or recovery-test results.
