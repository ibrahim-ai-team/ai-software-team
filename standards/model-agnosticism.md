# Model agnosticism and adapter boundary

## Source of truth

The Markdown files in `.claude/agents/*.md` define each agent's role, responsibilities, constraints, inputs, outputs, and evidence requirements. They are the source of truth for agent behavior. Runtime-specific adapters translate that contract into a target orchestrator's representation; adapters must not silently redefine role behavior or governance.

Claude Code remains supported. This is a portability boundary and documentation/validation guardrail, not a migration or a claim that all workflows are portable.

## Portability rules

- Keep role, purpose, inputs, outputs, responsibilities, constraints, handoffs, gates, and evidence in ordinary Markdown.
- Do not embed undocumented Claude Code-only control syntax in agent Markdown. Put runtime-specific implementation details in adapter-owned docs and explain why they cannot live in the shared contract.
- References to `.claude/agents/`, `.claude/skills/`, and `.claude/commands/` are real current coupling; this step documents them and does not rewrite them.
- Adapters must preserve human approval checkpoints, security restrictions, traceability, and evidence contracts.

## Prohibited patterns checked by the validator

| Pattern | Reason |
| --- | --- |
| `$ARGUMENTS` | Claude Code command argument substitution is runtime-specific |
| `$CLAUDE_[A-Z0-9_]+` | Claude Code environment variables are runtime-specific |
| `<tool-name>` or `<command-name>` | Claude Code transcript/control markers are not portable contracts |

These are narrow, high-confidence patterns, not a complete detector. A hit fails validation with the agent path and line number. If a future exception is required, document the exact pattern, file, and rationale here and add a narrowly scoped allowlist plus regression test. No exceptions are approved currently.

## Shared adapter interface

- `discoverAgents()`: return agent identifiers and parsed Markdown contract metadata.
- `delegate(agent, task)`: dispatch a task while preserving inputs, outputs, and restrictions.
- `runGate(gate)`: evaluate a named gate and return structured evidence, decision, and blockers.

This is a conceptual interface only; no adapter code is introduced by this change.
