---
name: security-threat-modelling
description: Use when reviewing trust boundaries, sensitive flows, or security risks.
---

# Identify threats and prioritize mitigations

## When to use

Use this skill before implementing authentication/authorization, sensitive data flows, external integrations, file uploads, payments, secrets, or privileged operations.

## Procedure

Map assets, trust boundaries, actors, entry points, and sensitive flows. Consider spoofing, tampering, repudiation, information disclosure, denial of service, and privilege escalation. Rank risks and propose practical mitigations.

## Expected outputs

- Assets, actors, entry points, trust boundaries, and sensitive flows
- Threats/abuse cases with severity, mitigations, and residual risk
- Verification tasks mapped to mitigations and any decision needed from the sponsor

## Quality checks

- Consider spoofing, tampering, repudiation, information disclosure, denial of service, and privilege escalation.
- Prefer concrete mitigations and testable controls over generic warnings.
- Escalate material residual risk; do not silently accept it on the user's behalf.
