---
name: architecture-evaluation-adr
description: Use when comparing architecture options or recording consequential decisions.
---

# Evaluate architecture choices and record decisions

## When to use

Use this skill during architecture design when boundaries, quality attributes, deployment topology, or a consequential technical choice needs evaluation.

## Procedure

Start from requirements and quality attributes. Compare viable options against constraints, costs, security, operability, and reversibility. Record context, alternatives, decision, consequences, and evidence in an ADR.

## Expected outputs

- Options compared against requirements, constraints, costs, and operational burden
- Recommended option with trade-offs and rejected alternatives
- ADR containing context, decision, consequences, and evidence

## Quality checks

- Do not choose a stack before requirements and constraints are understood.
- Prefer the simplest option that satisfies verified needs.
- Identify decisions requiring sponsor approval before implementation.
