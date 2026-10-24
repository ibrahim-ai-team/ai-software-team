# EARS Specification

> Author: business-analyst. Validator: product-owner. Human approver: CP1.
> The BA is the sole author of the final EARS specification. The PO provides and validates business value but does not rewrite the specification. Replace these instructions with story-specific content.

## Business value (PO)

- **Why — problem / expected value:**
- **For whom — target user/persona:**
- **Success metrics — success measure:**
- **Priority (P0/P1/P2):**
- **High-level scope — in scope:**
- **High-level scope — out of scope:**

## Specification (BA)

### Context

- **Story ID:**
- **Actors and environment:**
- **Assumptions:**
- **Dependencies:**
- **Glossary:**
- **Open questions:**

### Functional requirements (EARS)

Write each requirement as a testable EARS statement:
- **Event-driven:** `When <trigger>, the system shall <behavior>.`
- **State-driven:** `While <state>, the system shall <behavior>.`
- **Condition:** `If <condition>, then the system shall <behavior>.`

Examples (replace these):
- When a user submits valid credentials, the system shall create an authenticated session.
- If a payment is declined, then the system shall display a clear failure message and preserve the cart.
- While an account is locked, the system shall reject authentication attempts.

#### Story requirements

- EARS-01:
- EARS-02:

### Non-functional constraints

Record relevant measurable constraints (performance, availability, accessibility, privacy, security, compatibility, observability, and operational limits).

- NFR-01:
- NFR-02:

### Workflows and edge cases

- Happy path:
- Alternate paths:
- Edge cases:

### Acceptance criteria (Gherkin)

Use observable Given/When/Then scenarios linked to requirement IDs.

```gherkin
Feature: <capability>

  Scenario: <observable outcome>
    Given <initial context>
    When <trigger or action>
    Then <expected result>
```

### Requirement-to-test traceability matrix

| Requirement ID | Criterion / Gherkin scenario | Test ID |
| --- | --- | --- |
| EARS-01 | | |

### Out of scope

List behaviors and changes explicitly excluded from this story.

-
