# Portability audit: current Claude Code coupling

This audit reflects the repository's current `main` snapshot at the time of this PR. Priorities describe impact on a future non-Claude orchestrator, not security severity. Line references can shift in later commits and should be re-verified before being used as stable identifiers.

| File and line(s) | Actual coupling | Reason | Priority |
| --- | --- | --- | --- |
| `.claude/CLAUDE.md:1` | Claude Code instruction entry point | Other orchestrators do not automatically load this file or its instruction hierarchy. | blocking |
| `.claude/settings.json:1-5` | Claude Code `permissions.deny` syntax | Tool authorization rules must be translated; copying this JSON does not enforce policy in another runtime. | blocking |
| `.claude/agents/agile-orchestrator.md:1-12` | Agent directory layout and Claude-oriented metadata | Discovery/frontmatter semantics must be translated before another orchestrator can invoke the role. | blocking |
| `scripts/validate_team.py:12-20` | Validator defines Claude Code tool names and a specific orchestrator role | Validation enforces runtime-specific delegation and tool assumptions. | blocking |
| `.claude/skills/*/SKILL.md:1` (directory convention) | Skills use Claude Code's `SKILL.md` discovery layout | Another runtime needs a loader and skill-injection mapping. | blocking |
| `.claude/commands/*.md:1` (directory convention) | Commands use Claude Code's command directory | Slash-command discovery and argument handling are runtime-specific. | blocking |
| `.claude/agents/*.md` frontmatter (`tools`, `model`, `skills`; per-file lines vary) | Runtime metadata is colocated with Markdown role contracts | A generic parser must separate common fields from execution metadata. | blocking |
| `.github/workflows/validate-team.yml:1` (workflow invocation) | CI runs the Python validator that checks Claude Code structure | CI itself is portable, but validator assumptions need mapping for another runtime. | cosmetic |
| `README.md:1-3` | Project is described as a Claude Code starter kit | This is accurate today but should be broadened when another adapter is implemented. | cosmetic |

## What is not coupled yet

Most `standards/` and workflow documentation is plain Markdown and can inform future adapters, but behavioral assumptions still need semantic mapping and tests. The shared interface in `adapters/README.md` is proposed only. No DeepSeek API, LangGraph, or CrewAI adapter is delivered or claimed.

## Next audit step

For a real adapter, re-run this audit against its branch and demonstrate parity for agent discovery, delegation, gates, human checkpoints, permissions, and evidence before claiming portability.
