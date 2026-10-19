# First supervised pilot — readiness and board corrections

Assessed: 2026-10-19 against `main` `8bf343a`. Evidence for runtime results: [`verification-report.md`](verification-report.md). This is a dated snapshot; re-check GitHub before acting.

## Access limits during this assessment

- GitHub Project #1 (fields, views, item statuses): **not readable** — the session's GitHub integration exposes no Projects API, and `gh` has no valid token.
- Issues: readable, but create/edit/comment returned `403 Resource not accessible by integration`. No issue or board change was made.
- The corrections below are therefore a ready-to-apply list, not completed changes.

## Board audit (from issues, PRs and repository evidence)

| # | Finding | Correction |
|---|---|---|
| A1 | Status is encoded in titles (`[READY]` #24, `[IN PROGRESS]` #25, `[BLOCKED]` #26), contradicting the rule that the Project `Status` field is the only status source ([github-projects-setup.md](github-projects-setup.md)). Closed #28, #33, #37, #41 carry `[DONE]`. | Remove prefixes; set Project `Status` instead. |
| A2 | Org issue fields `Priority` and `Effort` exist but are empty on every open issue; priority lives only in body text (P1/P2). | Set fields (P0→Urgent, P1→High, P2→Medium, P3→Low). |
| A3 | #24 and #25 are labelled `bug`; they are verification tasks. | Remove `bug`. |
| A4 | #25 is stale: still says "run `claude --version` in Termux"; cloud-runtime evidence now exists. | In Review once the PR with `verification-report.md` is open. |
| A5 | #24 lacks the two concrete gaps now observed: no required checks on `main`, and GitHub MCP merge tools not denied. | Add both to #24 (no new issue). |
| A6 | #26 is `BLOCKED` on #25 and overlaps #38 (model routing, closed by PR #44's `model-routing-decision.md`). Budget/stop/retry defaults already exist in `workflows/orchestration-contract.md`. | Narrow to "calibrate sizing and budgets from pilot data"; Backlog, after pilot. |
| A7 | #32 was partly delivered by PR #44 (Markdown link checker in CI). | Narrow title to the remaining scope. |
| A8 | #43 is assigned but not in progress. | Unassign until picked up. |
| A9 | No card for the pilot itself. | Create IA-PILOT-01 (text below). |
| A10 | Agents cannot write Issues/Projects from the cloud session (403), but the pilot workflow depends on agents creating issues. | Owner action O3. |
| A11 | `docs/project-state.md` listed #23 as in progress and an old `main` SHA. | Updated in this branch. |
| A12 | `project-status.yml` (board automation) has never run. | Leave as #40; update the board manually during the pilot. |

No duplicates warrant closing: #40 (status workflow) and #42 (claiming) are distinct; #34/#35/#36/#39 are distinct owner/settings items.

### Card-by-card target state

| Issue | New title | Status | Priority | Effort | Other |
|---|---|---|---|---|---|
| [#24](https://github.com/ibrahim-ai-team/ai-software-team/issues/24) | IA-SEC-01 — Enforce PR + required CI on `main` and deny agent merge tools | In Progress | Urgent | Low | remove `bug`; add gaps A5 |
| [#25](https://github.com/ibrahim-ai-team/ai-software-team/issues/25) | IA-RUN-02 — Smoke-test Claude Code discovery, delegation, and permissions | In Review | Urgent | Low | remove `bug`; link PR |
| IA-PILOT-01 (new) | IA-PILOT-01 — Run the first supervised pilot from idea to first reviewed PR | Blocked (by #24, #25, O3) | High | Medium | body below |
| [#26](https://github.com/ibrahim-ai-team/ai-software-team/issues/26) | IA-BUD-03 — Calibrate sprint sizing and task budgets from pilot data | Backlog | Medium | Medium | depends on IA-PILOT-01 |
| [#42](https://github.com/ibrahim-ai-team/ai-software-team/issues/42) | (keep) | Backlog | Medium | Medium | needed only before parallel coding |
| [#32](https://github.com/ibrahim-ai-team/ai-software-team/issues/32) | Validate command references and agent frontmatter schema in CI | Backlog | Low | Low | note link check done in #44 |
| [#43](https://github.com/ibrahim-ai-team/ai-software-team/issues/43) | (keep) | Backlog | Low | Low | unassign |
| [#40](https://github.com/ibrahim-ai-team/ai-software-team/issues/40) | (keep) | Backlog | Low | Medium | |
| [#34](https://github.com/ibrahim-ai-team/ai-software-team/issues/34) | (keep) | Backlog | Low | Low | |
| [#35](https://github.com/ibrahim-ai-team/ai-software-team/issues/35) | (keep) | Backlog | Low | Low | |
| [#36](https://github.com/ibrahim-ai-team/ai-software-team/issues/36) | (keep) | Backlog | Low | Low | owner decision |
| [#39](https://github.com/ibrahim-ai-team/ai-software-team/issues/39) | (keep) | Backlog | Low | Low | |

Closed #23, #28, #33, #37, #38, #41: Status Done; optionally drop `[DONE]` from titles.

Views: keep the existing ones; ensure one view (e.g. "Pilot readiness") filters `is:open priority:Urgent,High` grouped by Status, and that "Product Backlog" shows all open items. Then confirm each issue above appears there with the intended Status.

## Launch checklist

| Criterion | Result | Evidence |
|---|---|---|
| Runtime discovery of agents, skills, commands | PASS (cloud) / NOT VERIFIED (local) | verification-report RT-01–04 |
| Actual subagent delegation and handoff | PASS (one read-only delegation) | RT-05 |
| Permission enforcement / sensitive files | PASS for tested deny rules; `ask` prompts NOT VERIFIED | RT-06–11 |
| Agent cannot merge | **FAIL** — MCP merge/auto-merge tools not denied | Gaps, #24 |
| Branch protection and required CI | **FAIL** — protected, but no required checks; PR rule not visible | Gaps, #24 |
| Human-controlled merging | NOT VERIFIED (policy + CODEOWNERS only) | #24 |
| Issue-based planning, AC, traceability | PASS (process docs/templates); **BLOCKED** for agent issue writes from cloud | A10 |
| Sprint sizing, budgets, checkpoints, stop conditions | PASS for a supervised pilot (defaults in orchestration contract) | `workflows/orchestration-contract.md` §Session and cost budget, §Retry |
| Safe branch/PR workflow, tests, independent review | PASS (CI green, 43 tests, read-only reviewer verified) | CI runs, RT-05 |
| Session resume and progress reporting | NOT VERIFIED at runtime (procedure documented) | IA-PILOT-01 AC |
| Concurrent-work conflict prevention | PASS for pilot via single-writer rule; no lock mechanism (by design) | orchestration contract; #42 |
| Board reflects reality | NOT VERIFIED — board unreadable | A1–A12 |

## Go / no-go

**Conditional GO** for a supervised pilot. Discovery, requirements and architecture can start as soon as O1–O3 are done; the first coding story waits for O4–O5 (merge-safety).

## Must-do before starting (dependency order)

1. **O3 — Agent write access to Issues/Projects** (owner): grant the Claude GitHub App *Issues: read & write* (and organization *Projects: read & write*) for the repositories the pilot uses, or run the pilot in a local Claude Code session with an authenticated `gh`. Without this the team cannot create the backlog itself.
2. **O4 — Branch protection on `main`** (owner, Settings → Branches → rule for `main`): require a pull request (0 approvals, since agents act under the owner's account); require status checks `Static configuration checks (Python 3.10)`, `(3.11)`, `(3.12)` and `Scan repository for secrets`; do not allow bypass; keep force-push and deletion disabled. Apply the same rule in the pilot application repository.
3. **O5 — Deny agent merge tools** (approve the proposal below; one small PR).
4. Merge the PR carrying this file and `verification-report.md` (closes the evidence part of #25).

### Proposal requiring approval (not implemented)

Add to `permissions.deny` in `.claude/settings.json`: `mcp__github__merge_pull_request` and `mcp__github__enable_pr_auto_merge`; add a validator assertion and test so CI fails if they are removed. Verify by attempting a merge call against a closed/nonexistent PR and recording the denial.

## Can wait until after the pilot

#26 (calibrate from real data), #42 (needed only for parallel coding), #40 (board automation; update manually), #32, #43, #34, #35, #36, #39; per-agent model overrides; local/Termux runtime re-test unless the pilot runs locally.

## First pilot sprint (proposal — no application work started)

| ID | Task | Owner | Depends on | Acceptance |
|---|---|---|---|---|
| P1 | Provide the idea (1–2 sentences) and application repo name/visibility | Sponsor | — | Recorded in the pilot issue |
| P2 | Discovery via `/kickoff` | product-owner, business-analyst | P1, O3 | Brief with problem, users, MVP scope, assumptions, questions; only material decisions escalated |
| P3 | Requirements and 3–5 stories with testable AC | business-analyst | P2 | Stories pass `workflows/backlog-quality-gates.md` Definition of Ready |
| P4 | Architecture and stack recommendation | software-architect (+ technical-research) | P3 | ≥1 ADR, threat-model checkpoint or N/A rationale, `/approve-gate` decision recorded |
| P5 | App board and issues per `per-app-project-blueprint.md` | project-manager | P3, O3 | Issues exist with Priority/Effort/Status; view shows them |
| P6 | `/plan-sprint` — commit ≤3 stories | project-manager | P4, P5 | Plan with budget, stop condition, single coding WIP |
| P7 | `/next-story` — implement one story | relevant developer + qa-automation | P6, O4, O5 | Feature branch, tests, CI green |
| P8 | `/review-pr` + PR for owner decision | code-review-security | P7 | Review findings dispositioned; PR open, not merged by agents |
| P9 | `/status`, `/handover`, resume in a new session, `/retro` | coordinator | P8 | Report matches GitHub; resume works; ≤3 findings filed here |

### IA-PILOT-01 issue text (to create)

Title: `IA-PILOT-01 — Run the first supervised pilot from idea to first reviewed PR`

Goal: prove the kit end to end on one small idea under owner supervision and turn what breaks into a short backlog. Blocked by #24, #25 and agent write access (O3). Scope: tasks P1–P9 above; at most 3 committed stories; one coding delegation at a time; stop and `/handover` on context pressure or after two failed retries; no paid services, deployments or new repositories without owner approval. Acceptance: the P2–P9 acceptance column, with links to discovery docs, issues, ADR, PR, CI run, review, handover and retro.
