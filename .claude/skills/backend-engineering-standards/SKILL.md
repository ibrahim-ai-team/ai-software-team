---
name: backend-engineering-standards
description: Use when implementing server-side business logic, APIs, or authorization.
---

# Implement maintainable and secure backend behavior

## When to use

Use this skill for server-side behavior, endpoints, integrations, data access, and authorization-sensitive code.

## Procedure

Keep business rules testable, validate at trust boundaries, authorize every sensitive operation server-side, handle errors consistently, avoid leaking secrets, and test normal and failure paths. Do not assume a framework.

## Expected outputs

- Small implementation scoped to approved behavior
- Tests for normal, invalid, unauthorized, and failure paths as relevant
- Notes on API/data contract changes and unresolved risks

## Quality checks

- Validate untrusted inputs at server-side trust boundaries.
- Enforce authorization on the server for each sensitive operation.
- Avoid exposing credentials, personal data, or internal error details in logs/responses.
