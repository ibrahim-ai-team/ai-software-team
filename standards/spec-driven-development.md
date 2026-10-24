# Spec-Driven Development (SDD) and EARS

## Mandatory rule

Every new story must have a completed, reviewed specification based on [`templates/spec-ears.md`](../templates/spec-ears.md) before it is considered ready for implementation. **A story without a validated EARS spec must not pass G1** in [the validation-gates standard](validation-gates.md). Do not delegate coding or begin implementation while the spec is absent, incomplete, or rejected.

## Ownership and validation

- **Authors:** `product-owner` and `business-analyst) collaborate to produce the EARS specification, including functional requirements, non-functional constraints, Gherkin acceptance criteria, assumptions, and out-of-scope boundaries.
- **Human checkpoint:** the human sponsor reviews and approves the product plan/specification at CP1 according to [the human-in-the-loop standard](human-in-the-loop.md).
- **Architecture validation:** the `software-architect` reviews the spec for feasibility, system boundaries, interfaces, security/privacy, and material technical constraints before G1.
- **G1 precondition:** the Gate reviewer verifies that the story links to the reviewed EARS spec and that its requirements are testable and consistent with acceptance criteria. If either the spec or required approval/review evidence is missing, G1 fails closed.
- **Changes:** material changes to scope or requirements require the spec and impacted acceptance criteria to be updated and reviewed before implementation continues.

## EARS requirement patterns

Use one or more of these patterns, as appropriate:

- Event-driven: `When <trigger>, the system shall <behavior>.`
- Conditional: `If <condition>, then the system shall <behavior>.`
- State-driven: `While <state>, the system shall <behavior>.`

Every requirement must describe observable behavior. Avoid vague statements such as “the system should be user-friendly” unless decomposed into measurable, testable requirements. Gherkin scenarios complement EARS statements; they do not replace the formal requirements.

## Required story flow

`Idea → Product Owner + Business Analyst → EARS spec → human CP1 + Software Architect review → G1 → implementation`

The spec test in `tests/test_spec_ears.py` checks that the EARS template contains at least one line starting with `When `, `If `, or `While ` and containing `shall`. This lightweight test is a format guard, not a substitute for human review, architecture review, or complete requirements validation.
