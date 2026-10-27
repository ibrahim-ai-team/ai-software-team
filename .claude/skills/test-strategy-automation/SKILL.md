---
name: test-strategy-automation
description: Designs a risk-based test approach across test levels, automation and quality gates. Use when planning or writing tests or defining quality gates.
---

# Design a risk-based testing approach

## When to use

Use this skill when defining a test strategy, selecting automation targets, investigating coverage gaps, or designing CI quality gates.

## Required inputs

The acceptance criteria and risk, the existing test levels and commands, the environments and test data available, and the CI constraints.
## Procedure

Map acceptance criteria to test levels. Prioritize fast unit, integration/contract, and API tests where appropriate; add UI and end-to-end tests for critical user journeys. Isolate data, avoid flakiness, and report evidence and gaps.

## Expected outputs

- Risk-based test levels and coverage mapped to acceptance criteria
- Test data, isolation, environment, and flakiness strategy
- Verification evidence, exclusions, and residual quality risks

## Quality checks

- Prefer fast unit, API, integration/contract checks where they provide appropriate coverage; reserve UI/E2E for key journeys.
- Keep tests independent and data isolated; avoid order-dependent suites.
- Report exactly which tests ran, passed, failed, or were unavailable.
