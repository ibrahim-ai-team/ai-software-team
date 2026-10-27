---
name: api-design-documentation
description: Designs consistent, secure API contracts with schemas, error models and compatibility rules. Use when defining or changing an API contract or its documentation.
---

# Design consistent and secure APIs

## When to use

Use this skill when creating or changing an HTTP/API contract, integration boundary, or API documentation.

## Required inputs

The requirement or story the API serves, the consumers, existing contracts and versioning policy, and the error and authorization model.
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
