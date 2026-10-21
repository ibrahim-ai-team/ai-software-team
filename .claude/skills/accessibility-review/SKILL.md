---
name: accessibility-review
description: Use when reviewing UI accessibility, keyboard operation, focus management, semantics, contrast, and assistive-technology compatibility.
---

# Review user-interface accessibility

## When to use

Use for new/changed user interfaces, forms, dialogs, navigation, interactive components, and accessibility acceptance criteria.

## Procedure

1. Identify applicable accessibility requirements and the tested page/component scope.
2. Inspect semantic HTML and accessible names, roles, states, and form error associations.
3. Check keyboard-only operation, logical focus order, visible focus, focus restoration, and no keyboard traps.
4. Review color contrast, zoom/reflow, text clarity, target sizes, reduced motion, and status announcements as applicable.
5. Run available automated checks and manual keyboard checks; state tool/browser limitations.
6. Report each finding with severity, affected component, reproduction steps, expected behavior, and recommendation.

## Expected outputs

- Scoped accessibility review and test evidence
- Findings with severity, reproduction steps, and remediation suggestions
- Unverified criteria and assistive technology/browser limitations

## Quality checks

- Distinguish automated scans from manual checks; neither alone proves full conformance.
- Do not claim WCAG conformance without a sufficiently scoped and evidenced assessment.
- Prioritize barriers that prevent access to critical journeys.
