---
name: security-threat-modelling
description: Identifies trust boundaries, threats and abuse cases and ranks mitigations by risk. Use when designing or reviewing authentication, authorization, sensitive data flows, secrets or other security-relevant changes.
---

# Identify threats and prioritize mitigations

## When to use

Use this skill before implementing authentication/authorization, sensitive data flows, external integrations, file uploads, payments, secrets, or privileged operations.

## Required inputs

The data flows and trust boundaries, the assets and data classification, authentication/authorization design, and the external integrations. If a required input is missing, stop and ask the orchestrator for it instead of assuming it.

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
