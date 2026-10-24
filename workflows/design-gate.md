# Mandatory UI/UX design gate

## When the gate is required

The orchestrator must require a design handoff before frontend implementation when a task introduces or materially changes any of:

- a user journey, navigation path, or screen;
- layout, visual hierarchy, or design-system behavior;
- responsive behavior or supported viewport behavior;
- user interactions, forms, validation, or meaningful UI states.

For a truly minor change with no material design impact, the orchestrator may record an exception only when the designated decision authority approves it. The durable handoff record is still required, including the rationale, approver and approval evidence; the artifact itself may be N/A only for this approved exception. A skill invocation, verbal claim, or generic note is not a design artifact.

## Required handoff

Create a durable handoff record using `templates/design-handoff-template.md` and link it from the User Story and frontend task. It must include:

- User Story reference and the acceptance criteria covered;
- a real Figma URL when Figma is available and appropriate, or a concrete repository artifact path/URL;
- responsive behavior, interaction details, and applicable loading, empty, error, success, validation, accessibility and keyboard states;
- an explicit `Approval status: approved`, the approver, and durable approval evidence;
- QA verification scope and evidence.

Never invent a Figma URL. If Figma is unavailable or inappropriate, provide a concrete alternative such as an annotated wireframe or implementation-ready design specification. Explain the reason and record approval. An exception to Figma does not waive the requirement for a traceable artifact when design work is needed.

## Stop conditions

Frontend implementation must not begin while any of these is true:

- the required handoff is missing;
- the artifact is a placeholder or cannot be located;
- acceptance criteria are not mapped to the handoff;
- approval status is not explicitly `approved`;
- approval evidence or approver is missing;
- a Figma exception lacks rationale or approval.

The orchestrator owns the gate and must verify evidence rather than relying on an agent's statement. QA compares implementation against the approved handoff and records deviations or explicit non-applicability.

## Ownership

- UI/UX designer: prepares the flow/specification and artifact.
- Product sponsor/designated decision authority: approves the artifact or documented exception.
- Frontend: implements only after the gate passes.
- QA: validates responsive states, interactions and applicable accessibility/UI states.
- Orchestrator: confirms all evidence is linked before marking frontend work Ready.
