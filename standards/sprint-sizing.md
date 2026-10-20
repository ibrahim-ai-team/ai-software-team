# Sprint sizing and task budgets

Version 1, 2026-10-20. Costs come from the measured runs in `docs/verification-report.md` (BUD-03); turn-cap enforcement from BUD-01. All caps and estimates are v1. Recalibrate after the first pilot sprint (#45), using that sprint's measured costs.

## Sponsor settings (owner decisions, 2026-10-20)

| Setting | Value |
|---|---|
| Billing | Claude subscription (Pro/Max): usage limits that reset, no per-call bill |
| Sprint length | 2 weeks |
| Sprint budget | about **$10 API-equivalent** per sprint |
| Sessions per sprint | about 4–6 (the team works only while a Claude Code session is open) |

On a subscription, "$" means **API-equivalent cost**: the `total_cost_usd` that Claude Code reports for headless runs, or an estimate from the table below. It is a size measure, not a charge. Subscription usage limits can stop a session before the budget is reached; treat that as a normal checkpoint.

## Story points and size

Score each task on scope, uncertainty, dependencies, test burden and risk, and use the highest:

| Points | Size | Effort field | Typical task | Rule |
|---|---|---|---|---|
| 1 | XS | Low | Copy, config or doc change in one file; known pattern | — |
| 2 | S | Low | One endpoint, component or migration with its tests | — |
| 3 | M | Medium | A story slice touching up to ~5 files, with tests | Default size for implementation tasks |
| 5 | L | High | Several components, or one real unknown | Allowed only after a spike or Tech Lead breakdown confirms the approach |
| 8 | XL | High | Too big or too uncertain | **Must be split** before it can be Ready |

`tech-lead` assigns points during the breakdown; `project-manager` sums them for capacity.

## Budget per delegation

| Delegation | Turn cap (enforced) | Estimated cost (API-eq.) | Basis |
|---|---|---|---|
| Planning or analysis (PO, BA, architect, UX, PM, research, docs) | 25 | $0.05–0.15 | Measured: 4 planning delegations plus orchestration $0.34 (BUD-03) |
| Read-only review (`tech-lead`, `code-review-security`) | 40 | $0.05–0.20 | Measured: one small read-only delegation $0.07 (BUD-03); larger diffs need chunked reads |
| Specialist checks (performance, SRE, release) | 40 | $0.20–0.60 | Estimate |
| Implementation XS–S (backend, frontend, database, DevOps, QA) | 60 | $0.20–0.50 | Estimate: recalibrate in pilot |
| Implementation M | 60 | $0.50–1.00 | Estimate: recalibrate in pilot |
| Implementation L | 60, plus at most one re-delegation | $1.00–2.00 | Estimate: recalibrate in pilot |
| Session resume / status report | — | about $0.05 | Measured: $0.05 (BUD-03) |

A **story** costs its implementation tasks plus about **$0.50** of overhead: QA validation, two reviews and orchestration. A typical M story is therefore about **$1–1.50**.

## Sprint capacity

```
plan budget   = sprint budget × 0.8                 # keep 20% for rework and surprises
budget limit  = floor(plan budget ÷ cost per story)  # $8 ÷ ~$1.5 → 5 M-stories
session limit = sessions per sprint × 1              # about one story finished per session
capacity      = min(budget limit, session limit)     # counted in stories
```

Points do not enter the formula. They decide which stories may be committed: an 8 must be split, and a 5 needs a confirmed breakdown. After a few sprints, points per sprint (velocity) can replace the cost estimate. With the current settings, capacity is about 4–5 M-stories. **The first pilot sprint commits at most 3**, until real costs are measured.

## What is enforced and what is policy

| Control | Type | Evidence |
|---|---|---|
| `maxTurns` in each agent's frontmatter | **Enforced by Claude Code**: the agent stops at the cap and returns a "stopped at its N-turn limit" note | BUD-01: a 2-turn agent stopped after 2 tool calls |
| `--max-budget-usd` on headless runs (`claude -p`) | Documented by the CLI for headless runs only; a stop at the cap has not been observed | Claude Code 2.1.303 `--help`: "only works with --print" (BUD-02) |
| `--max-turns` on headless runs | Accepted by the CLI in the test runs but not listed in `--help`; a stop at the cap has not been observed | BUD-02 |
| Sprint budget, size estimates, thresholds below | Team policy, applied by `agile-orchestrator` | Not enforced; agents cannot read their own cost in interactive sessions |
| Subscription usage limits | Enforced by the subscription | Outside this kit's control |

## Stop and checkpoint rules

- **Delegation hits its turn cap:** if the partial result shows progress, the orchestrator may re-delegate once: a narrower task to the same role, with the partial result as input. Otherwise split the task, or mark it `BLOCKED` with the evidence. A re-delegation counts against the budget. (The orchestrator's tools do not include `SendMessage`, so a capped agent is not resumed in place.)
- **70% of the sprint budget used:** report it in the daily report, and finish in-flight work before starting new stories.
- **90% used:** start nothing new; finish or hand over in-flight work; ask the sponsor whether to stop, cut scope or raise the budget.
- **Over budget:** only with the sponsor's explicit yes for this sprint.
- **Two failed retries of the same step:** stop and report (see `workflows/orchestration-contract.md`).
- **Session ending or context pressure:** write the handover (`/handover`) before stopping.

## Tracking

- Each delegation record (`templates/agent-delegation-template.md`) has a size, turn cap, estimated cost, measured cost (if known) and continuations.
- The sprint plan (`templates/sprint-plan-template.md`) has the budget, capacity and the commitment.
- The daily report (`templates/daily-project-report-template.md`) has the budget used and its source: **measured** for headless runs, otherwise **estimated**.
- At sprint review, compare estimates with measured costs and update the tables above.
