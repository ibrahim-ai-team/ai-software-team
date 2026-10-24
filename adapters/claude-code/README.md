# Claude Code adapter — current coupling

## Status

Claude Code is the current supported execution environment. This folder documents existing coupling; it does not contain an adapter implementation. Agent Markdown defines role contracts, while discovery, delegation, tools, permissions, commands, and skills currently depend on Claude Code conventions.

## Coupling points

- `.claude/agents/*.md` uses the Claude Code agent directory layout and runtime metadata.
- `.claude/CLAUDE.md` is a Claude Code instruction entry point.
- `.claude/settings.json` expresses Claude Code-specific tool allow/deny/ask permission rules.
- `.claude/skills/*/SKILL.md` and `.claude/commands/*.md` use Claude Code discovery conventions.
- Agent frontmatter fields such as `tools`, `model`, and `skills` may be interpreted by Claude Code rather than a generic Markdown parser.
- Orchestration/delegation uses Claude Code's Agent tool and named tools; the validator enforces an allowlist of those names.

See [the portability audit](../../docs/portability-audit.md). No DeepSeek, LangGraph, or CrewAI adapter is implemented by this PR.
