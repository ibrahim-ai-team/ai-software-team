---
description: Start discovery for a new software project without implementing prematurely
---

# Project kickoff

Run this as `agile-orchestrator` (start Claude Code with `claude --agent agile-orchestrator`, then give the idea or type `/kickoff <idea>`). The orchestrator delegates; it does not write the requirements itself.

1. Read `workflows/orchestration-contract.md`, `workflows/project-bootstrap.md`, and `workflows/agile-agent-delivery.md` (`.claude/CLAUDE.md` is already loaded).
2. Treat this command as team configuration/orchestration only unless the user explicitly gave an application idea and authorized project bootstrap.
3. For an application idea, delegate discovery to `product-owner` and `business-analyst`; capture users, problem, outcomes, functional and non-functional needs, constraints, assumptions, risks, and open questions. Read the `requirements-analysis` and `user-stories-acceptance-criteria` skills when shaping the requirements.
4. Ask only material questions that block safe direction. Record reversible assumptions and continue.
5. Then delegate architecture to `software-architect` (options, ADR, stack recommendation with trade-offs) and a buildability check to `tech-lead`. Do not hard-code a stack before requirements are known.
6. Produce a concise discovery summary and proposed next phase. Do not generate application code until discovery/specification and sponsor gates in the workflow are satisfied.
7. Record durable state and next actions in the project state file when one exists. Never claim GitHub Issues/Projects were updated unless verified.
