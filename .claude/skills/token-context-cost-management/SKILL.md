---
name: token-context-cost-management
description: Keeps delegations bounded and context small to save subscription usage. Use when planning delegations, managing context pressure or controlling execution cost.
---

# Manage context and usage efficiently

## When to use

Use this skill before multi-agent tasks, long sessions, large research jobs, or work with token/time/cost constraints.

## Required inputs

The task to delegate, the session and usage limits in `standards/sprint-sizing.md`, and the context already established that the delegate needs.
## Procedure

Work within the Claude Pro subscription's five-hour and weekly usage limits; never switch to API billing or buy extra usage. Break work into bounded tasks, load only relevant files, reuse existing skills and templates, summarize durable decisions, and hand off concise context. Run one delegation at a time and avoid redundant agent calls. Apply the token-saving practices and stop rules in `standards/sprint-sizing.md`, and stop to ask when missing information changes the result.

## Expected outputs

- Bounded task plan with expected deliverables and stopping condition
- Minimal context/file loading plan and checkpoint/handover strategy
- Observed usage facts: delegations run, turn caps hit, sessions used, usage-limit warnings

## Quality checks

- Set explicit delegation/WIP limits and avoid duplicate agent calls.
- Do not invent token counts, model prices, or usage telemetry.
- Stop starting new work when a usage-limit warning or context pressure threatens verification or handover.
- No dollar or API-equivalent budgets, API keys or API credits.
