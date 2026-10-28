---
name: ui-ux-design-system
description: Designs implementation-ready user flows, screens, interactions, responsive layouts and design-system patterns. Use before building a new journey or a material UI change.
disable-model-invocation: true
---

# Design implementation-ready user experiences

## When to use

Mandatory before frontend implementation for a new user journey, material layout/visual decision, responsive behavior, or interaction change. For genuinely minor changes with no meaningful design impact, document why the gate is not required and obtain designated approval. Follow `workflows/design-gate.md`; invoking this skill is not itself a completed design deliverable.

## Required inputs

The user stories and journeys, the target devices and accessibility level, and the existing design system or brand constraints.

## Procedure

1. Read the approved User Story and acceptance criteria; record the story link and acceptance criteria covered in the handoff.
2. Identify the user goal and critical path.
3. Map the flow and alternate/error paths. Mark assumptions and questions instead of inventing requirements.
4. Describe screen hierarchy, component behavior, responsive breakpoints, and reusable patterns consistent with the existing design system.
5. Specify loading, empty, error, success, validation, and destructive-action states as applicable.
6. Include keyboard interaction, focus behavior, semantic controls, contrast/readability, and reduced-motion considerations.
7. Hand off the artifact/specification to frontend and QA, linked to the story and acceptance criteria. Record approver and approval evidence. QA must verify applicable responsive breakpoints, interactions, accessibility, and loading/empty/error/success states against the approved artifact; report anything not applicable with a rationale.

## Expected outputs

- User-flow and screen/component specification
- Responsive and interaction-state requirements mapped to acceptance criteria
- Design decisions, assumptions, open questions, and implementation handoff

## Quality checks

- Critical and alternate flows are covered; missing product decisions are visible.
- Design guidance is feasible with the current stack and component system.
- UI states and responsive behavior are explicit rather than implied.
- Do not claim usability validation or research that was not performed.
