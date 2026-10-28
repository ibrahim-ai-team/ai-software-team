---
name: debugging-root-cause-analysis
description: Finds root causes from reproduction and evidence before fixing. Use when diagnosing a reproducible defect, a failing build or an unstable test.
disable-model-invocation: true
---

# Find root causes with evidence

## When to use

Use this skill for a bug, failing check, flaky test, unexpected behavior, or recurring incident.

## Required inputs

A reproduction (failing test, CI log or steps), the commit or environment where it fails, and the last known good state if any.

## Procedure

Reproduce the issue, capture observable evidence, narrow hypotheses, and change one variable at a time. Distinguish root cause from symptoms. Add a regression check and document what was verified.

## Expected outputs

- Reproduction steps and observable evidence
- Ranked hypotheses with the evidence that supports or rejects each
- Root cause, minimal fix, regression check, and remaining uncertainty

## Quality checks

- Reproduce before changing code when practical; preserve logs and exact commands.
- Change one relevant variable at a time and distinguish symptoms from causes.
- Add a regression check and report when reproduction or verification was impossible.
