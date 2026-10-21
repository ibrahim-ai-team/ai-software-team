---
name: api-design-documentation
description: Use when defining API contracts, schemas, errors, or compatibility.
---

# Design consistent and secure APIs

## When to use

Use this skill when creating or changing an HTTP/API contract, integration boundary, or API documentation.

## Procedure

Define resources, methods, request/response schemas, status codes, validation, authentication, authorization, pagination, idempotency, versioning, and error format. Document examples and compatibility risks. Test contracts.

## Expected outputs

- Resource/operation and request/response schema table
- Authentication, authorization, validation, error, pagination, and idempotency rules where applicable
- Example requests/responses and compatibility notes

## Quality checks

- Define behavior for invalid input and unauthorized access.
- Check compatibility and versioning impact before changing existing contracts.
- Map each contract requirement to a test or explicitly state the gap.
