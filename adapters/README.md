# Adapters

This directory documents the portability boundary. Agent Markdown remains the source of truth; adapters translate it into the target orchestrator's runtime model.

## Planned and existing adapters

- **claude-code — existing:** current runtime using `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/CLAUDE.md`, and `.claude/settings.json`. See [Claude Code adapter notes](claude-code/README.md).
- **deepseek-api — planned:** provider/API-backed adapter. Not implemented; no compatibility is claimed.
- **langgraph — planned:** graph/state-machine orchestration adapter. Not implemented.
- **crewai — candidate:** to evaluate after the shared contract and gates stabilize. Not implemented.

## Common interface

1. `discoverAgents()` — discover Markdown contracts and return identifiers plus metadata.
2. `delegate(agent, task)` — dispatch a task and preserve context, restrictions, and evidence.
3. `runGate(gate)` — run a named gate and return a decision with evidence and blockers.

This is a proposed conceptual interface, not an implemented API. Implementations must preserve human approval, branch/PR policy, least privilege, and traceability. See [the portability audit](../docs/portability-audit.md).
