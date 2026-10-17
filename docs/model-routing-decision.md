# Agent Model Routing Policy

## Decision status

**Status: DEFERRED pending runtime and official-documentation verification.**

The reusable team does not hard-code a `model` field into every agent profile. Model identifiers, aliases, account availability and routing behavior can change. A static repository audit cannot prove that a model name is accepted by the installed Claude Code version or available to the user.

## Interim policy

1. Use the installed Claude Code default unless a verified, documented need justifies a per-agent override.
2. Before adding an override, check current official Claude Code documentation and test the exact value in the installed version.
3. Prefer the least expensive model that reliably meets the task's quality and safety requirements.
4. Reserve stronger reasoning/capability for architecture trade-offs, security-sensitive review, ambiguous requirements and complex debugging when supported and justified.
5. Do not route every agent to a premium model by default or assume model aliases from old examples remain valid.
6. Record the model identifier, Claude Code version, date checked, task category, expected benefit, fallback, and any measured cost/quality evidence.
7. Keep user/API credentials and billing details out of committed files.

## Evaluation checklist

- [ ] Confirm supported model syntax and aliases in current official documentation.
- [ ] Record installed Claude Code version and account constraints.
- [ ] Test one low-risk documentation task and one representative reasoning task.
- [ ] Compare quality, latency and usage/cost using available usage evidence.
- [ ] Decide whether each override is worth maintaining.
- [ ] Add validator coverage only after an explicit schema and supported-value policy exist.

## Revisit trigger

Re-evaluate when Claude Code changes model-routing support, account availability changes, or observed task quality/cost no longer meets project needs.

This policy is a decision record, not proof that any model routing has been tested.
