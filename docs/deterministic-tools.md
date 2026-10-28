# Deterministic tools

Mechanical work goes to scripts: validation, file discovery, comparisons, fixed algorithms, check execution. Agents keep the judgment: what a result means, what to do about it, and every design or product decision. A script's output is evidence for that judgment, never a replacement for it.

"Who" lists the roles the scope hook (`scripts/enforce_agent_scope_hook.py`) lets run the tool through Bash; "human/CI" tools run in pre-commit, CI or the sponsor's terminal. Every listed tool is read-only unless the "Writes" column says otherwise.

## Delegation and review

| Tool | Who | Use when | The LLM still decides | Writes |
| --- | --- | --- | --- | --- |
| `scripts/route_model.py` | orchestrator | Before each delegation, to get the model tier | The primary skill, size, and whether the change is security-sensitive or a retry | — |
| `scripts/enforce_agent_scope.py` | orchestrator | Before a write delegation, per allowed path | Which paths the task needs | — |
| `scripts/check_diff_scope.py` | orchestrator | When an agent returns changes, and on the final branch | Whether an out-of-scope edit is rejected or isolated | — |
| `scripts/relevant_lessons.py` | any agent | Before every delegation | Which lessons apply beyond the story match | — |
| `scripts/add_lesson.py` | orchestrator | After a failed G1 or G2, before retrying | The sanitized lesson text | `.claude/lessons/lessons.md` (append-only) |
| `scripts/check_claims.py` | orchestrator | Before dispatching a delegation | Reassignment after recovery | — |
| `scripts/coordinator_lock.py` | orchestrator | At session start (`acquire`) and end (`release`) | Whether to wait for or report a held lock | `state/coordinator.lock` |
| `scripts/new_worktree.sh` | orchestrator | Before a writing delegation | — | a worktree in `../worktrees/` |

## Gates and approvals

| Tool | Who | Use when | The LLM still decides | Writes |
| --- | --- | --- | --- | --- |
| `scripts/detect_conflict.py` | orchestrator | Before every transition | How to frame the escalation | — |
| `scripts/check_approvals.py` | orchestrator | Before crossing CP1–CP4 | Nothing: a non-zero exit stops the transition | — |
| `scripts/check_gates.py` | orchestrator | Before coding (G1) and merge readiness (G2, with `--commit`) | Nothing: a non-zero exit stops the transition | — |
| `scripts/detect_checks.py` | `ci-verifier`, orchestrator | Before running checks for G2 | Whether the evidence supports G2 (`code-review-security`) | — |
| allowlisted checks (`python -m unittest`, `ruff`, `gitleaks`, `npm`, `make`) | `ci-verifier` | The commands `scripts/detect_checks.py` lists | Same as above | — |

## Sprint, release and status

| Tool | Who | Use when | The LLM still decides | Writes |
| --- | --- | --- | --- | --- |
| `scripts/check_governance.py` | orchestrator, `project-manager`, `release-manager` | Sprint records, design handoffs (`--frontend-readiness`), release (`--release`) | Plans, priorities and go/no-go recommendations | — |
| `scripts/status_report.py` | orchestrator, `project-manager` | Mid-session status | What the status means for the plan | — |
| `scripts/provision_project.py` | orchestrator (`plan`, `apply`) | `/provision-project` | The plan contents; `apply` also needs the sponsor's prompt and approval record | GitHub resources on `apply` |
| `scripts/roi_report.py`, `scripts/analyze_telemetry.py` | human/CI | Sprint review and reporting (printed to stdout) | Interpretation | — |
| `scripts/status_snapshot.py` | human/CI | Refreshing the status snapshot | Interpretation | `state/effective.json` |
| `scripts/claim_task.py`, `scripts/list_claims.py`, `scripts/release_claim.py` | human/CI | Atomic claims across machines (optional) | — | claim refs on the remote |
| `scripts/cleanup_worktree.sh` | human only | After a story is merged | — | removes a worktree |

## Repository validation (pre-commit and CI)

| Tool | Use when | Checks |
| --- | --- | --- |
| `scripts/validate_team.py` | Any change to agents, skills, commands, templates or settings | Inventory, frontmatter, permissions, required files |
| `scripts/check_cross_references.py` | Any change to agents or commands | Named agents, skills, commands and paths exist |
| `scripts/check_markdown_links.py` | Any Markdown change | Local links and their anchors, including backticked file-with-anchor references |
| `scripts/check_placeholders.py` | Planning artifacts | Unresolved placeholders |
| `scripts/check_licenses.py` | Dependency changes | License risk |
| `scripts/smoke_discovery.py` | Any change to the inventory | Offline inventory check |
| `scripts/verify_telemetry.py` | Telemetry audits | The telemetry hash chain |

These do not prove runtime behavior: they validate files. Claude Code discovery and delegation are verified by the probes in `docs/evals/agent-definition-evals.md`.

## Adding a tool

Add a script only when the task is mechanical, has one correct answer, and an LLM would otherwise read or compare files to get it. Keep it read-only where possible, fail closed on bad input (exit `2`), add tests, add an exact pattern to `ALLOWED_SCRIPTS` in the hook for the roles that need it, and list it here.
