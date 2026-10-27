# Agent Capabilities and Runtime Caveats

This kit contains 18 agent profile files: `agile-orchestrator` (run as the main session with `claude --agent agile-orchestrator`) and 17 specialists. Their presence as Markdown files does not prove runtime discovery or guarantee that all agents can be spawned in parallel. Actual capabilities depend on installed Claude Code version, settings, permissions, and available tools.

The `description` frontmatter is intended to help routing. Agent definitions intentionally do not hard-code a project stack. Skills are shared procedural references and do not grant permissions by themselves.

Use the fewest agents needed for each task. The coordinator should not delegate merely to simulate activity.

## Tool allowlists (least privilege)

Each agent declares an explicit `tools:` allowlist in its frontmatter; the static validator requires it. Allowlists are a starting point and should be tightened per project.

| Agent group | Tools | Rationale |
| --- | --- | --- |
| Orchestrator (`agile-orchestrator` only) | Agent, Read, Grep, Glob, Edit, Write, Bash | Delegates to specialists; the validator rejects `Agent` on any other agent, so specialists cannot spawn agents |
| Implementation and delivery roles | Read, Grep, Glob, Edit, Write, Bash | Implement changes and run checks where authorized |
| Planning/documentation roles | Read, Grep, Glob, Edit, Write | Prepare requirements, plans and documentation |
| Read-only review roles (`code-review-security`, `tech-lead`) | Read, Grep, Glob | Inspect code and return findings or breakdowns as text; the orchestrator writes files. Enforced by the allowlist, and the validator rejects Edit/Write/Bash on these agents |
| Technical research | Read, Grep, Glob, WebSearch, WebFetch | Research current sources and return recommendations; no direct file writes |

Consult each agent's own frontmatter as the source of truth for its exact allowlist; the groups above are explanatory, not an authorization mechanism.

## Model selection

Each specialist declares a `model` alias in its frontmatter: `opus` for `software-architect` and `code-review-security`, `haiku` for `ci-verifier` and `github-integration`, `sonnet` for the others. `agile-orchestrator` inherits the session model. Rationale, fallback and pending runtime verification: [Agent Model Routing Policy](model-routing-decision.md).

## Verification

Unverified at runtime: tool names, agent discovery and permission enforcement depend on the installed Claude Code version. Confirm in a real session and record results in `docs/verification-report.md`.
