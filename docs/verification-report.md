# Verification Report

Record only observed results. Static checks do not prove runtime behavior, and one runtime does not prove another (for example, a cloud session does not prove a local Termux/desktop installation).

## Run 2026-10-19 — Claude Code cloud session (issue #25 / #24)

- **Runtime:** Claude Code `2.1.303`, managed cloud session (Linux container) with this repository checked out at `main` `8bf343a` plus the readiness branch. Permission mode: auto-approval with a session safety layer, so some denials below may come from the session layer rather than only from `.claude/settings.json`.
- **Not covered:** a local CLI/Termux installation, interactive approval prompts for `ask` rules, hooks, and model routing.

### Static package checks

| Check | Command | Result |
|---|---|---|
| Inventory and security config | `python3 scripts/validate_team.py` | PASS (16 agents, 23 skills, 11 commands, 17 templates) |
| Discovery fixture | `python3 scripts/smoke_discovery.py` | PASS (static file check only) |
| Regression tests | `python3 -m unittest discover -s tests` | PASS, 43 tests |
| CI on `main` `8bf343a` | [Validate](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39077920728), [Secret scanning](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39077920727) | success |

### Runtime checks

| ID | Case | Observed | Result |
|---|---|---|---|
| RT-01 | `.claude/CLAUDE.md` loaded | Project instructions were injected into the session context | PASS |
| RT-02 | Agent discovery | All 16 project agents were offered as delegation targets | PASS |
| RT-03 | Skill discovery | All 23 project skills were listed as invocable | PASS |
| RT-04 | Command discovery | All 11 project commands (`kickoff`, `plan-sprint`, `next-story`, `review-pr`, `status`, `handover`, …) were listed | PASS |
| RT-05 | Delegation `SMOKE-DEL-01` to `code-review-security` | Subagent returned a report; its tools were exactly `Read, Grep, Glob` (matching frontmatter); it had no write/shell tool and correctly quoted the first line of `README.md` | PASS |
| RT-06 | `Read(./.env)` (file absent) | Denied: "denied by your permission settings"; control read of another absent file returned "does not exist" | PASS |
| RT-07 | `Read(./secrets/**)` (file absent) | Denied by permission settings | PASS |
| RT-08 | `git push --force` to a nonexistent local path | Denied before execution | PASS (source of denial not distinguishable) |
| RT-09 | `gh pr merge` against a nonexistent repository | Denied before execution | PASS (source of denial not distinguishable) |
| RT-10 | Writing a fake `.env` fixture via Bash | Denied by the session safety layer; no repository rule covers shell redirection | INFO |
| RT-11 | `ask` rules (Edit of `.claude/settings.json`, workflows, CODEOWNERS) | Not attempted, to avoid an unreviewed change to protected files | NOT RUN |
| RT-12 | Deny `mcp__github__merge_pull_request` and `mcp__github__enable_pr_auto_merge` (#24, 2026-10-19) | After the rules were added to `.claude/settings.json`, the running session reloaded settings, reported the merge tool as "Denied by a permission rule" and removed both tools from the available set | PASS (cloud session; settings on a feature branch until merged) |

### Gaps found

- **GitHub MCP merge tools were not denied** (closed by RT-12 once merged). `.claude/settings.json` denied `gh pr merge` but not `mcp__github__merge_pull_request` / `mcp__github__enable_pr_auto_merge`. Agents act under the owner's GitHub identity, so branch protection cannot distinguish an agent merge from an owner merge. Tracked in #24.
- **Branch protection on `main` (`GET branches/main/protection`, 2026-10-19):** PR required with 1 approval and code-owner review; force pushes and deletions blocked; **no required status checks**; `enforce_admins` off; no rulesets. Because agents act under the owner's account, merges rely on the admin bypass. Tracked in #24.
- **GitHub Project #1:** not reachable from cloud sessions (GraphQL and org Project endpoints return 403 by design); `project-status.yml` has never run. Board state: NOT VERIFIED.
- **Issues:** after the Claude GitHub App install, issue create/edit/comment succeeded and were read back (#45 created).

## Run 2026-10-19 — Project status workflow and board read-back (#40)

Workflow `.github/workflows/project-status.yml` from branch `claude/ai-team-project-readiness-td7x2s`, dispatched via `workflow_dispatch`, `PROJECTS_TOKEN` present.

| ID | Case | Observed | Result |
|---|---|---|---|
| PS-01 | Issue not on the Project (#45) | Failed with "Issue #45 is not on Project ibrahim-ai-team/#1" ([run](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39297846952)) | PASS (clear error) |
| PS-02 | Real update #24 → Blocked | Updated, then read back "actual Project Status 'Blocked'" ([run](https://github.com/ibrahim-ai-team/ai-software-team/actions/runs/39297917731)) | PASS |
| PS-03 | `dry_run` on 18 issues | Reported each Status without changing it; `Done → Blocked` refused as an invalid transition | PASS |
| PS-04 | `add_if_missing` (#35, #45) | Added both issues to the board, then set Ready / Blocked with read-back | PASS |
| PS-05 | Full chain Ready → In Progress → In Review → Approved → Done for #32, #34, #35, #39, #40, #42, #43 | Every step read back; Done gate verified merged PR #48 with `Closes #n` | PASS |

Board Status read back on 2026-10-19 before corrections (Project #1):

| Status | Issues |
|---|---|
| Blocked | #24, #26 |
| In Progress | #25 (issue closed: board out of sync; the Done gate needs a merged PR that says `Closes #25`, so the owner moves it by hand or enables the Project's "Item closed → Done" workflow) |
| Backlog | #32, #34, #36, #39, #40, #42, #43 |
| Done | #23, #28, #33, #37, #41 |
| Not on board | #35, #38, #45 (no auto-add workflow on the Project) |

Board Status after corrections (each value confirmed by the workflow's read-back):

| Status | Issues |
|---|---|
| Blocked | #24 (owner branch rule), #45 (pilot) |
| Backlog | #26, #36 |
| In Progress | #25 — closed issue; owner action (see above) |
| Done | #23, #28, #32, #33, #34, #35, #37, #39, #40, #41, #42, #43 |
| Not on board | #38 (closed; cosmetic) |

## Template for future runs

### Static package checks
- Agent files present:
- Skill files present:
- Required templates/standards present:
- Validator output:

### Runtime checks (only after running Claude Code)
- Claude Code version and environment:
- Agents discovered:
- Skills discovered:
- Any schema warnings:
- Actual task delegation tested? Evidence:
- Permissions/tool availability (per case: denied / prompted / allowed):
- Limitations and manual setup:
