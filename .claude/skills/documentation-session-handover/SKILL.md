---
name: documentation-session-handover
description: Writes technical docs, status reports and resumable session handovers that separate verified facts from unverified claims. Use when documenting setup or behavior, reporting progress, or ending a session.
disable-model-invocation: true
---

# Keep documentation and handovers actionable

## When to use

Use this skill when updating README/setup/operations docs, recording decisions, writing reports, or handing work to a future session.

## Required inputs

The reconciled project state, the delegation records and their evidence (PRs, CI runs), and the open decisions and blockers.

## Procedure

Document verified setup, decisions, changed files, checks and exact outcomes, unresolved questions, blockers, and the next one to three actions. Label assumptions and unverified runtime behavior.

## Expected outputs

- Documentation tied to verified behavior and source files
- Decisions, limitations, checks/results, and unresolved questions clearly labeled
- Next one to three actions with owner and evidence links

## Quality checks

- Do not document intended behavior as implemented behavior without evidence.
- Label assumptions, unverified runtime behavior, and checks not run.
- Keep handover concise enough for the next session to resume without rereading the full conversation.
