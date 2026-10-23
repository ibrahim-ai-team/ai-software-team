---
name: performance-testing
description: Use when designing load, stress, spike, endurance, scalability, or performance regression tests.
---

# Measure system performance reproducibly

## When to use

Use when latency, throughput, concurrency, capacity, resource efficiency, or performance regression is part of the acceptance criteria.

## Required inputs

Measurable performance requirements (latency, throughput, budgets), a representative environment and data set, and the baseline to compare with. If a required input is missing, stop and ask the orchestrator for it instead of assuming it.

## Procedure

1. Define target journeys/endpoints, workload assumptions, concurrency, ramp-up, duration, test data, and explicit pass/fail thresholds.
2. Confirm the target environment and obtain approval before stressing shared or production systems.
3. Record application version/commit, hardware/environment, configuration, warm-up, test command/tool, and workload profile.
4. Capture latency distributions (p50/p95/p99 as appropriate), throughput, error rate, saturation, and CPU/memory/database/network signals where available.
5. Compare runs only when environment and workload are sufficiently comparable; identify confounders.
6. Investigate bottlenecks using evidence, propose targeted changes, and rerun the same workload after changes.
7. Summarize limitations, failures, regressions, and recommended repeatable CI checks.

## Expected outputs

- Reproducible performance test plan and safe execution boundaries
- Scripts/configuration and exact commands when implementation is assigned
- Results with workload, environment, latency, throughput, errors, resource evidence, and limitations
- Bottleneck findings and proposed regression thresholds

## Quality checks

- Thresholds are declared before results are interpreted.
- No performance numbers are fabricated; unavailable telemetry is identified.
- Before/after claims use comparable workloads and environments.
- Stop if the target is unauthorized or the test risks service disruption or unexpected cost.
