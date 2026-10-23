---
name: ui-ux-design-system
description: Use when defining user flows, screen structure, interaction behavior, responsive layouts, or reusable design-system patterns.
---

# Design implementation-ready user experiences

## When to use

Use for new or changed user-facing flows, navigation, forms, complex states, visual consistency, and design handoff before or alongside frontend implementation.

## Required inputs

The user stories and journeys, the target devices and accessibility level, and the existing design system or brand constraints. If a required input is missing, stop and ask the orchestrator for it instead of assuming it.

## Procedure

1. Read approved user stories and acceptance criteria; identify the user goal and critical path.
2. Map the flow and alternate/error paths. Mark assumptions and questions instead of inventing requirements.
3. Describe screen hierarchy, component behavior, responsive breakpoints, and reusable patterns consistent with the existing design system.
4. Specify loading, empty, error, success, validation, and destructive-action states as applicable.
5. Include keyboard interaction, focus behavior, semantic controls, contrast/readability, and reduced-motion considerations.
6. Hand off a concise specification to frontend and QA; review implementation against the agreed specification if requested.

## Expected outputs

- User-flow and screen/component specification
- Responsive and interaction-state requirements mapped to acceptance criteria
- Design decisions, assumptions, open questions, and implementation handoff

## Quality checks

- Critical and alternate flows are covered; missing product decisions are visible.
- Design guidance is feasible with the current stack and component system.
- UI states and responsive behavior are explicit rather than implied.
- Do not claim usability validation or research that was not performed.
