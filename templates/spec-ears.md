# EARS Specification

> Use this template for every new story before backlog readiness. Replace all guidance text with story-specific content. Do not treat examples as requirements for the actual story.

## Context

- **Story ID:**
- **Problem / user need:**
- **Actors and environment:**
- **Assumptions:**
- **Dependencies:**

## Functional requirements (EARS)

Write each requirement as one testable EARS statement. Use the appropriate pattern:

- **Event-driven:** `When <trigger>, the system shall <behavior>.`
- **State-driven:** `While <state>, the system shall <behavior>.`
- **Unwanted behavior / condition:** `If <condition>, then the system shall <behavior>.`

### Examples

When a user submits valid credentials, the system shall create an authenticated session.
If a payment is declined, then the system shall display a clear failure message and preserve the cart.
While an account is locked, the system shall reject authentication attempts.

### Story requirements

- EARS-01:
- EARS-02:

## Non-functional constraints

Record measurable constraints for performance, availability, accessibility, privacy, security, compatibility, observability, and operational limits as applicable.

- NFR-01:
- NFR-02:

## Acceptance criteria (Gherkin)

Use observable Given/When/Then scenarios linked to requirement IDs.

```gherkin
Feature: <capability>

  Scenario: <observable outcome>
    Given <initial context>
    When <trigger or action>
    Then <expected result>
```

## Out of scope

List behaviors and changes explicitly excluded from this story.

-
