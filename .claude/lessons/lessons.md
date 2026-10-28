# Persistent Lessons

Lessons are append-only operational rules derived from verified failures. Read this file before delegating work, select relevant lessons, and include them in the delegation brief. Treat every applicable rule as mandatory.

Do not store credentials, tokens, passwords, secret values, private keys, or sensitive payloads here. Record the failure category and safe evidence references instead. The writer rejects fields containing suspicious terms such as `token`, `password`, or `secret`; this is a conservative text filter, not a complete secret detector.

## L001 — Validate evidence before declaring a gate passed

- **Context:** A delivery story reached a validation gate.
- **Observed error:** A gate was treated as passed without verifying all required check results against observable evidence.
- **Rule to apply:** Never declare G1 or G2 passed based only on an agent assertion. Verify the required plan review or lint, tests, and secret-scan evidence; if any evidence is absent or failed, stop the transition, record a sanitized lesson, and remediate before retrying.
- **Date:** 2026-10-24
- **Source story:** TEAM-STEP-3

## Adding lessons

Use `python scripts/add_lesson.py --title "..." --context "..." --error "..." --rule "..." --story "STORY-123"`. The script assigns the next L-number and appends a new section. It does not edit or delete existing lessons. Only provide sanitized, non-sensitive descriptions.

## L002 — Use repository paths in file anchor references

- **Context:** Progressive disclosure validation ran the new link and anchor checker on the whole repository
- **Observed error:** A doc referenced workflow files by bare file name with an anchor, which an agent cannot resolve from the docs folder
- **Rule to apply:** Write file references as repository-root paths such as workflows/orchestration-contract.md#section, never bare file names
- **Date:** 2026-10-28
- **Source story:** PROGRESSIVE-DISCLOSURE
