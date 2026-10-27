---
name: architecture-evaluation-adr
description: Compares architecture options against quality attributes and records the decision as an ADR. Use when choosing system boundaries or making a consequential, hard-to-reverse technical decision.
---

# Evaluate architecture choices and record decisions

## When to use

Use this skill during architecture design when boundaries, quality attributes, deployment topology, or a consequential technical choice needs evaluation.

## Required inputs

Requirements and quality attributes (NFRs), constraints (budget, hosting, team skills), existing ADRs, and the decision to be made. If a required input is missing, stop and ask the orchestrator for it instead of assuming it.

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
