# Agent Capabilities and Runtime Caveats

This kit contains 16 agent profile files. Their presence as Markdown files does not prove runtime discovery or guarantee that all agents can be spawned in parallel. Actual capabilities depend on installed Claude Code version, settings, permissions, and available tools.

The `description` frontmatter is intended to help routing. Agent definitions intentionally do not hard-code a project stack. Skills are shared procedural references and do not grant permissions by themselves.

Use the fewest agents needed for each task. The coordinator should not delegate merely to simulate activity.

## Tool allowlists (least privilege)

Each agent declares an explicit `tools:` allowlist in its frontmatter; the static validator requires it. Allowlists are a starting point and should be tightened per project.

| Agent group | Tools | Rationale |
|---|---|---|
| Implementation and delivery roles | Read, Grep, Glob, Edit, Write, Bash | Implement changes and run checks where authorized |
| Planning/documentation roles | Read, Grep, Glob, Edit, Write | Prepare requirements, plans and documentation |
| Read-only review roles | Read, Grep, Glob | Inspect code without direct edits or shell execution |
| Technical research | Read, Grep, Glob, WebSearch, WebFetch | Research current sources and return recommendations; no direct file writes |

Consult each agent's own frontmatter as the source of truth for its exact allowlist; the groups above are explanatory, not an authorization mechanism.

## Model selection

Per-agent model routing is intentionally deferred until supported values and behavior have been verified against the installed Claude Code version. See [Agent Model Routing Policy](model-routing-decision.md).

## Verification

Unverified at runtime: tool names, agent discovery and permission enforcement depend on the installed Claude Code version. Confirm in a real session and record results in `docs/verification-report.md`.
