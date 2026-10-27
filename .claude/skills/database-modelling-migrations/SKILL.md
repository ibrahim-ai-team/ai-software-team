---
name: database-modelling-migrations
description: Models data and evolves schemas with reversible, safe migrations and integrity constraints. Use when designing schemas, queries, data integrity rules or migrations.
---

# Model data and evolve schemas safely

## When to use

Use this skill when adding or changing entities, relationships, indexes, constraints, queries, or database migrations.

## Required inputs

The data requirements, current schema and migrations, data volume and retention constraints, and the rollback expectation. If a required input is missing, stop and ask the orchestrator for it instead of assuming it.

## Procedure

Define entities, relationships, constraints, indexes, and retention needs from requirements. Make migrations repeatable and safe; consider locks, data volume, backfills, rollback, and compatibility with deployed code.

## Expected outputs

- Schema/data model with constraints and ownership assumptions
- Migration plan including rollout, backfill, rollback, and compatibility where relevant
- Integrity/query tests and operational risks

## Quality checks

- Assess lock duration, data volume, and backward compatibility for deployed code.
- Make migrations repeatable and safe; avoid destructive changes without explicit approval.
- Verify constraints and failure/rollback behavior, not only the happy path.
