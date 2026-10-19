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

### Gaps found

- **GitHub MCP merge tools are not denied.** `.claude/settings.json` denies `gh pr merge`, but in sessions with the GitHub MCP server the tools `mcp__github__merge_pull_request` and `mcp__github__enable_pr_auto_merge` are available and not covered. Because agents act with the owner's GitHub identity, branch protection cannot tell an agent merge from an owner merge. Tracked in #24.
- **Branch protection on `main` (`GET branches/main/protection`, 2026-10-19):** PR required with 1 approval and code-owner review; force pushes and deletions blocked; **no required status checks**; `enforce_admins` off; no rulesets. Because agents act under the owner's account, merges rely on the admin bypass. Tracked in #24.
- **GitHub Project #1:** not reachable from cloud sessions (GraphQL and org Project endpoints return 403 by design); `project-status.yml` has never run. Board state: NOT VERIFIED.
- **Issues:** after the Claude GitHub App install, issue create/edit/comment succeeded and were read back (#45 created).

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
