# Sprint sizing and usage limits

Version 2, 2026-10-20. Replaces the dollar budgets of version 1. Turn-cap enforcement comes from BUD-01 in `docs/verification-report.md`. Caps and capacity are v2 defaults. Recalibrate them after the first pilot sprint (#45), using that sprint's observed delegations and sessions.

Contents: planning a sprint → [points](#story-points-and-size), [turn caps](#usage-per-delegation), [capacity](#sprint-capacity); running a session → [stop rules](#stop-and-checkpoint-rules), [token-saving practices](#token-saving-practices); background → [operating model](#operating-model-claude-pro-subscription-only), [enforcement](#what-is-enforced-and-what-is-policy), [free infrastructure](#free-infrastructure-first), [tracking](#tracking).

## Operating model: Claude Pro subscription only

| Setting | Value |
| --- | --- |
| Plan | Claude Pro, used through Claude Code. No Claude API, API keys, API credits or extra-usage purchases |
| Sprint length | 2 weeks |
| Sessions per sprint | about 4–6 (a few times a week; nothing runs while Claude Code is closed) |
| Usage units | sessions, delegations per session, and each agent's enforced turn cap. No dollar or "API-equivalent" budget |

What the subscription gives (from Anthropic's support pages; re-check them, since limits change):

- Usage is limited by a **five-hour session limit** and a **weekly limit**. Both are shared with claude.ai chat, so chat use reduces what is left for the team.
- Claude Code warns as a limit approaches. `/status` shows the remaining allocation. `/usage` shows plan usage bars and what consumed them (skills, subagents, MCP servers).
- Pro may offer a short "Usage limit reached · wrapping up" grace once per weekly period. Do not plan for it.
- If `ANTHROPIC_API_KEY` is set, Claude Code bills that API key instead of the subscription. **Never set it** in this project's environment, settings or scripts. Decline any prompt to buy API credits or extra usage. Only the sponsor can decide to pay.
- The session cost figure Claude Code prints is for API users and is not relevant on Pro. Do not record it as a budget.

Sources: [Using Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan), [About usage limits](https://support.claude.com/en/articles/11647753-understanding-usage-and-length-limits), [Manage costs effectively](https://code.claude.com/docs/en/costs).

## Story points and size

Score each task on scope, uncertainty, dependencies, test burden and risk, and use the highest:

| Points | Size | Effort field | Typical task | Rule |
| --- | --- | --- | --- | --- |
| 1 | XS | Low | Copy, config or doc change in one file; known pattern | — |
| 2 | S | Low | One endpoint, component or migration with its tests | — |
| 3 | M | Medium | A story slice touching up to ~5 files, with tests | Default size for implementation tasks |
| 5 | L | High | Several components, or one real unknown | Allowed only after a spike or Tech Lead breakdown confirms the approach |
| 8 | XL | High | Too big or too uncertain | **Must be split** before it can be Ready |

`tech-lead` assigns points during the breakdown; `project-manager` sums them for capacity.

## Usage per delegation

Every delegation uses subscription usage: the subagent reads its own context, and its result returns to the orchestrator. Delegate only when a role's expertise or a separate context window helps.

| Delegation | Turn cap (enforced) | Typical count per story |
| --- | --- | --- |
| Planning or analysis (PO, BA, architect, UX, PM, research, docs) | 25 | 0–1; planning happens once per sprint, not per story |
| Read-only review (`tech-lead`, `code-review-security`) | 40 | 2 (one of each) |
| Specialist checks (performance, SRE, release) | 40 | 0; only when the story's acceptance criteria need them |
| Implementation XS–M (backend, frontend, database, DevOps, QA) | 60 | 1–2, including QA validation |
| Implementation L | 60 + at most one re-delegation | 2–3 |

A typical M story uses about **4–5 delegations**: implementation, QA, two reviews, and sometimes one planning or fix delegation.

## Sprint capacity

```text
delegation limit = 4–6 delegations per session     # one story's delegations, plus resume and report
session limit    = sessions per sprint × 1          # about one story finished per session
capacity         = session limit − 1 reserve        # 4–6 sessions → 3–5 stories
```

Points do not enter the formula. They decide which stories may be committed: an 8 must be split, and a 5 needs a confirmed breakdown. After a few sprints, points per sprint (velocity) can replace the session count. **The first pilot sprint commits at most 3 stories**, until real usage is observed.

## What is enforced and what is policy

| Control | Type | Evidence |
| --- | --- | --- |
| `maxTurns` in each agent's frontmatter | **Enforced by Claude Code**: the agent stops at the cap and returns a "stopped at its N-turn limit" note | BUD-01: a 2-turn agent stopped after 2 tool calls |
| Five-hour and weekly usage limits | **Enforced by the subscription**; Claude Code warns before the limit | Anthropic support pages above; outside this kit's control |
| Delegations per session, one active delegation, capacity | Team policy, applied by `agile-orchestrator` | Not enforced; agents cannot read their own usage |
| `--max-budget-usd`, `--max-turns` | Headless (`claude -p`) options; not part of this operating model | BUD-02: not used |

## Token-saving practices

From Anthropic's [cost guidance](https://code.claude.com/docs/en/costs), applied to this team:

- **Inspect before working.** Resume from `docs/project-state.md`, the handover and the open Issues and PRs. Do not repeat planning, research or reviews that already have a recorded result and no new information.
- **One task per session thread.** Use `/clear` between unrelated tasks, and `/compact` with a focus instruction when a long task must continue.
- **Small, specific prompts.** Give each delegation exact files, paths and acceptance checks; do not ask it to "look at the whole repository".
- **Right-size the model.** Each role has a default model tier, and each delegation is routed by the complexity of its primary skill, size and risk (`docs/model-routing-decision.md`).
- **Short always-loaded context.** Keep `.claude/CLAUDE.md` under about 200 lines and put procedures in on-demand skills.
- **Few tools.** Prefer the `gh` CLI or the project-status workflow over extra MCP servers, and turn off MCP servers a session does not need.
- **Push verbose output away from the main thread.** Let the implementing agent run tests and read logs, and return a summary with the exact commands and results.
- **No idle loops.** Do not schedule check-ins, polling or `/loop` while waiting. Each one resends the whole context. End the session and resume later.

## Stop and checkpoint rules

- **Delegation hits its turn cap:** if the partial result shows progress, the orchestrator may re-delegate once: a narrower task to the same role, with the partial result as input. Otherwise split the task, or mark it `BLOCKED` with the evidence. (The orchestrator's tools do not include `SendMessage`, so a capped agent is not resumed in place.)
- **Delegation limit reached for the session (about 6):** finish the in-flight story or hand it over; start nothing new.
- **Claude Code warns that a usage limit is near, or `/status` shows little left:** start nothing new, write the handover and the end-of-session report, and stop. Resume in the next session after the limit resets.
- **Usage limit reached mid-task:** the next session resumes from the last checkpoint. Never buy extra usage or switch to an API key without the sponsor's explicit decision.
- **Two failed retries of the same step:** stop and report (see `workflows/orchestration-contract.md`).
- **Session ending or context pressure:** write the handover (`/handover`) and the end-of-session report before stopping.

## Free infrastructure first

- Choose free and open-source tools and free tiers by default (see `.claude/skills/technology-stack-selection/SKILL.md`). Any paid service, plan upgrade or spending is a sponsor decision.
- **GitHub Actions:** on GitHub Free, private repositories get 2,000 Actions minutes per month across the organization; public repositories use standard runners for free. Usage over the free quota is billed if a payment method allows it. Keep CI jobs short, run them on pull requests rather than on every push to every branch, and cache dependencies. Repositories stay private by default; the sponsor may choose public for a project. See [GitHub Actions billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions).

## Tracking

- Each delegation record (`templates/agent-delegation-template.md`) has a size, turn cap, whether the cap was hit, and re-delegations.
- The sprint plan (`templates/sprint-plan-template.md`) has the sessions planned, capacity and the commitment.
- The daily report and the end-of-session report (`templates/daily-project-report-template.md`) record sessions used, delegations this session, and any usage-limit warning.
- At sprint review, compare planned and actual sessions and delegations per story, and update the tables above.
- The dollar figures in `docs/verification-report.md` (BUD-03) are historical test evidence. They are not used for planning.
