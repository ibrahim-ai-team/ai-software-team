# AI Software Team

A reusable, project-independent starter kit for coordinating AI-assisted software delivery with Claude Code. It contains agent definitions, skills, engineering standards, templates, and workflows—not an application.

## What is included

| Area | Contents |
| --- | --- |
| Agents | 20 roles under `.claude/agents/`: one `agile-orchestrator` plus specialists (see [team roles](#team-roles)) |
| Skills | 23 reusable procedures under `.claude/skills/` (the manifest minimum is 22) |
| Shared instructions | `.claude/CLAUDE.md` and local permission guardrails in `.claude/settings.json` |
| Standards | Engineering, security, Git workflow, and definition of done |
| Templates | 17 template files; 10 are currently required by the manifest, while the rest are optional support artifacts |
| Workflow and docs | Project bootstrap, Agile delivery, orchestration contract, agent traceability, GitHub Projects setup, capabilities, and verification notes |
| Validation | Manifest-driven Python static checks, offline inventory check, and regression tests |
| Security automation | Gitleaks secret scanning and weekly GitHub Actions dependency update PRs |

## Prerequisites

- Python 3.10+ for the static validator (standard library only).
- Claude Code installed and authenticated to verify actual agent/skill discovery. Follow the current official [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/overview).
- GitHub is optional for local use; GitHub Actions runs static checks on pushes and pull requests.

## Quick start

1. Clone or download this repository.
2. From the repository root, run `python scripts/validate_team.py`, `python scripts/smoke_discovery.py` (offline inventory check only), and `python -m unittest discover -s tests -v`.
3. The orchestrator filters persistent lessons before each delegation with `python scripts/relevant_lessons.py --story <story-id> --max 5`; only relevant, bounded results enter the brief.
4. Start the team from this directory with `claude --agent agile-orchestrator`. This makes the orchestrator the main session; it delegates to the specialists.
5. To check the setup only, ask it to report which agents and skills it discovers. To start a project, give it your idea (next section).

For a fictional end-to-end illustration, see [Example Walkthrough](docs/example-walkthrough.md). The example is documentation, not runtime evidence.

## Team roles

One orchestrator coordinates; specialists do the work and return results to it. Only the orchestrator can delegate. GitHub execution is always delegated to `github-integration`.

| Role | Agent file |
| --- | --- |
| Agile Orchestrator (entry point) | `.claude/agents/agile-orchestrator.md` |
| Product Owner | `.claude/agents/product-owner.md` |
| Business Analyst | `.claude/agents/business-analyst.md` |
| Scrum Master / Project Manager | `.claude/agents/project-manager.md` |
| Architect | `.claude/agents/software-architect.md` |
| Tech Lead | `.claude/agents/tech-lead.md` |
| Frontend / Backend Developer | `.claude/agents/frontend-developer.md`, `.claude/agents/backend-developer.md` |
| QA Engineer | `.claude/agents/qa-automation.md` |
| DevOps Engineer | `.claude/agents/devops-platform.md` |
| CI Verifier | `.claude/agents/ci-verifier.md` (Read + Bash only; closed verification command allowlist; no file writes) |
| Code / Security Reviewer | `.claude/agents/code-review-security.md` (read-only) |
| GitHub integration | `.claude/agents/github-integration.md` (delegated, execution-only Issues, PRs, board status and approved provisioning) |
| Used when needed | `database-engineer`, `ui-ux-designer`, `technical-research`, `performance-engineer`, `sre-observability-engineer`, `release-manager`, `documentation-manager` |

Shared rules for every specialist: [`standards/agent-contract.md`](standards/agent-contract.md).

## Spec-Driven Development (SDD/EARS)

Every new story starts with a formal specification using [`templates/spec-ears.md`](templates/spec-ears.md) before it enters the backlog. The Product Owner defines business value (why, persona, success metrics, priority, high-level scope); the Business Analyst alone writes the final EARS specification, workflows, Gherkin criteria, and requirement-to-test traceability. The PO validates business alignment without rewriting the spec. The human sponsor approves the plan at CP1 and the Software Architect reviews feasibility; a story without a validated spec cannot pass G1. See [`standards/spec-driven-development.md`](standards/spec-driven-development.md).

## Isolation & concurrence

Writing agents must use one dedicated Git worktree per agent and story. The orchestrator creates it before dispatch with `./scripts/new_worktree.sh <agent> <story>`; agents write only inside the supplied worktree and never write directly to `main`. Clean up after the story with `./scripts/cleanup_worktree.sh <agent> <story>`; the command requires explicit confirmation. See [`standards/agent-isolation.md`](standards/agent-isolation.md). Requires Git 2.5+, Bash, and standard POSIX utilities; supported on Linux, macOS, and WSL. Run `bash tests/test_worktree.sh` to exercise creation and cleanup.

## Spec-Driven Development (SDD / EARS)

Every new story starts with a completed EARS specification before backlog readiness. The Business Analyst writes it using [`templates/spec-ears.md`](templates/spec-ears.md), based on the Product Owner's value brief; the PO validates it without rewriting it; the Software Architect validates feasibility, and the human sponsor approves the specification at CP1. A story without a validated EARS spec and recorded CP1 approval cannot pass G1. See [`standards/spec-driven-development.md`](standards/spec-driven-development.md) and `tests/test_spec_ears.py` for the format guard.

## Mesure du ROI

At the end of each sprint, the Project Manager records story-level agent minutes, token counts, and estimated equivalent human hours in `.claude/metrics/sprint-<N>.json`. Generate the local Markdown report with `python scripts/roi_report.py --sprint 3`; optional overrides are `--rate-hourly 80` and `--token-cost 0.000003`. The script uses only the Python standard library and makes no network calls. See `.claude/metrics/README.md` for the input schema.

**Manual calculation example:** for 125,000 tokens at $0.000003/token, token cost is 125,000 × 0.000003 = $0.375. If equivalent human work is estimated at 2.5 hours and the rate is $80/hour, human cost is 2.5 × $80 = $200. The ROI ratio is $200 ÷ $0.375 = **533.33**. This is a cost comparison, not net profit; it excludes agent runtime and other infrastructure costs.

## GitHub Projects status — manual by design

GitHub Projects V2 board Status and views are updated **manually by design**. This repository does not ship automatic board-status synchronization: the available cloud execution path cannot reliably trigger and verify a workflow run on `main` with organization Project access. Do not assume changing an issue automatically changes its Project Status; update the board explicitly and verify the result.

## Agile commands

A new idea becomes its own GitHub workspace named after the app you propose (for example `shopinow-management`, `shopinow-front`, `shopinow-back`) with one Project board through `/provision-project`; see [project provisioning](docs/project-provisioning.md). This repository is never copied per application.

The available prompts include `/kickoff`, `/provision-project`, `/plan-sprint`, `/next-story`, `/review-pr`, `/status`, `/daily-report`, `/handover`, `/approve-gate`, `/sprint-review`, `/retro`, and `/release-check`. See [the command reference](docs/agile-command-reference.md). Commands run only when invoked in Claude Code; they are not background jobs.

## Give the team an idea

When ready to start an application, describe it in plain language, for example: "Build an e-commerce website where customers can browse products, purchase items, and track orders."

The team should perform discovery, requirements, architecture options, backlog preparation, test strategy and delivery planning, then implement incrementally through bounded tasks, isolated branches and PRs. The user supervises progress and makes material sponsor decisions; the team owns routine planning and coordination. The human owner alone merges PRs.

For the exact phases, recovery rules, evidence requirements and safety boundaries, read `workflows/orchestration-contract.md`, then `workflows/project-bootstrap.md` and `workflows/agile-agent-delivery.md`.

## Canonical lifecycle state machine

`models/status.py` is the executable source of truth for the `ProjectPhase`, `TaskStatus`, and `DelegationStatus` enums and their allowed transitions. Use `validate_transition(kind, src, dst)` to fail closed on invalid transitions, or `is_valid_transition(...)` for a boolean check. The Markdown contracts document the state vocabulary and workflow context; they must not introduce alternate code-level definitions.

Validate a transition from the repository root:

```bash
python scripts/check_governance.py --transition TaskStatus READY CLAIMED
```

The checker exits non-zero for unknown states, unknown kinds, or transitions not explicitly allowed. See [`workflows/orchestration-contract.md`](workflows/orchestration-contract.md#state-machine), [`workflows/project-status-transitions.md`](workflows/project-status-transitions.md#allowed-transitions-and-evidence), and [`docs/agent-traceability.md`](docs/agent-traceability.md#state-model) for the documented vocabulary.

## Important security limits

- `.claude/settings.json` defines client-side permission deny rules for selected dangerous commands and sensitive file paths. These are defense-in-depth, not a substitute for GitHub permissions, branch protection, or careful review. Test behavior in the installed Claude Code version.
- `.gitignore` reduces accidental tracking of common local secret files but cannot remove secrets already committed.
- Gitleaks runs in GitHub Actions; separately enable GitHub Secret Scanning and Push Protection where available.
- Configure and verify GitHub rulesets/branch protection and permissions separately. Do not treat the human-merge rule in documentation as technical enforcement.
- The validation workflow uses read-only repository permissions and disables persisted checkout credentials.

## Atomic task claiming via Git refs

Use Git's remote ref update as the atomic test-and-set primitive for task ownership; no GitHub API, token, lock server, or broker is required. Each claim is an orphan commit containing a `claim.json` payload, published at `refs/claims/<task-id>`. The remote accepts only one first creation of a given claim ref when the caller uses the empty `--force-with-lease` expectation.

From a local clone with the target remote configured:

```bash
python scripts/claim_task.py --task-id T-123 --run-id RUN-456
python scripts/list_claims.py --remote origin
python scripts/release_claim.py --task-id T-123 --remote origin
```

`claim_task.py` also accepts `--remote origin` (the default) and `--dry-run`. Set `AGENT_ID` and `SESSION_ID` to supply those identity values; otherwise the agent is recorded as `unknown` and a session UUID is generated. If `--run-id` is omitted, `RUN_ID` is used when set, otherwise a UUID is generated. Reuse the same run ID for retries that should be treated as the same run.

Exit codes for `claim_task.py`:

- `0`: claim acquired, or already held by the same `run_id` (idempotent retry).
- `1`: another `run_id` owns the task; the message identifies the recorded holder.
- `2`: invalid arguments or task ID.
- `3`: remote/network Git operation failed; retry is appropriate.

`release_claim.py` removes `refs/claims/<task-id>` and treats an already-absent ref as success when the remote accepts the deletion. `list_claims.py` lists remote claim refs and parses their JSON payloads. A claim remains active until explicitly released; there is no lease expiry or automatic cleanup, so release claims in a finally/cleanup path and reconcile abandoned claims manually. Claims are scoped to the remote repository and depend on the remote allowing custom Git refs. The existing `scripts/check_claims.py` remains a local pre-flight validator; the remote claim ref is the authority for atomic ownership.

## Single coordinator policy

The local coordinator lock makes the documented single-coordinator rule explicit. At the **start of each coordinator session**, before reconciling state or delegating work, run:

```bash
python scripts/coordinator_lock.py acquire
```

The default TTL is 3,600 seconds (one hour); choose a longer TTL for a longer session with `python scripts/coordinator_lock.py acquire --ttl 7200`. Inspect the current holder with `python scripts/coordinator_lock.py status`. If `acquire` exits with code `2`, stop coordinating while another non-expired holder owns the lock. At the **end of the session**, after saving the handover and Project Manager report, run:

```bash
python scripts/coordinator_lock.py release
```

The lock file is `state/coordinator.lock` and is local to one machine. An expired lock is reported with a warning and may be taken over; pick a TTL longer than the expected session because this is not a heartbeat. **This is not a distributed lock:** two coordinators running on different machines are not mutually excluded, and this mechanism does not protect shared remote resources.

## Important limits

- This repository does not itself run a background agent team when Claude Code is closed.
- Markdown task records and GitHub labels are not atomic distributed locks. The documented protocol is single-coordinator/single-writer unless separate isolated worktrees and a real coordination mechanism are configured.
- The validator reads `.claude/manifest.json` for minimum agent/skill inventories and required command/template files. The offline `scripts/smoke_discovery.py` checks whether inventory files and agent/skill metadata can be discovered without launching Claude Code. Neither check proves real Claude Code discovery, delegation, application correctness, deployment, or branch protection.
- Licensed under the [MIT License](LICENSE): free to use, copy, modify and share, including in your own applications, provided the copyright notice is kept. Applications built with this kit choose their own licence.

## Telemetry

Orchestration events are recorded locally in the append-only JSONL file `.claude/telemetry/activity.jsonl`, which is ignored by Git. The schema, secret-safety rules, and limitations are documented in [standards/telemetry.md](standards/telemetry.md).

Append a delegation event:

```bash
python scripts/append_telemetry.py \
  --agent agile-orchestrator \
  --action delegate \
  --story US-123 \
  --details '{"target":"qa-automation"}'
```

Analyze the events:

```bash
python scripts/analyze_telemetry.py
```

The writer adds an ISO 8601 timestamp and preserves the existing `agent` and UUID4 `trace_id` fields. It rejects invalid JSON and sensitive keys containing `token`, `password`, `api_key`, or `secret`, including nested objects. Never pass secrets to telemetry commands.

Telemetry uses a SHA-256 hash chain for **tamper-evidence, not cryptographic immutability**. Each event stores `prev_hash` and `event_hash`; the verifier detects content edits, broken links, deleted middle records, and legacy records without hashes. Run `python scripts/verify_telemetry.py` to verify the local log. A hash chain is not a blockchain, does not prevent someone from rewriting the entire file and recomputing every hash, and does not authenticate who wrote an event. The telemetry file is local and ignored by Git; preserve trusted external checkpoints if you need stronger audit evidence.

### Execution identity and legacy migration

Every new event also includes UUID4 `session_id`, `run_id`, and `event_id`, plus a validated canonical `agent_id` from `state/agents.json`. Use `--agent-id` or `AGENT_ID`; the existing `--agent` argument remains supported. Pass the same `--session-id`/`SESSION_ID` for all events in one session and the same `--run-id`/`RUN_ID` for all events in one run. If omitted, those IDs are generated for that invocation; `event_id` is always unique per event. Existing JSONL records are not rewritten: `analyze_telemetry.py` reads them and counts any event missing one or more identity fields as legacy.

## Apprentissage continu

The team maintains persistent, append-only lessons in [`.claude/lessons/lessons.md`](.claude/lessons/lessons.md). Before every delegation, the orchestrator reads the lessons and includes applicable rules in the brief. Lessons are binding constraints, not optional advice.

When a G1 or G2 validation Gate fails, preserve the failure evidence and add a sanitized lesson **before retrying**:

```bash
python scripts/add_lesson.py \
  --title "Verify gate evidence" \
  --context "A delivery story reached validation" \
  --error "A required check did not pass" \
  --rule "Verify all required evidence before advancing" \
  --story "SHOP-12"
```

The script assigns sequential IDs (`L001`, `L002`, ...), appends rather than overwriting, and rejects empty fields or text containing suspicious markers such as `token`, `password`, or `secret`. This conservative filter is not a complete secret detector: sanitize lesson text manually and never include credentials, secret values, or raw logs. Existing lessons must never be deleted or edited to hide a failure.

## Portabilité

Les contrats d'agents Markdown sont la source de vérité ; les intégrations d'exécution doivent les traduire sans perdre les gates, les permissions ni les validations humaines. Claude Code is the current integration. DeepSeek API et LangGraph sont prévus, mais pas implémentés. Voir [l'audit de portabilité](docs/portability-audit.md), le [standard d'agnosticisme](standards/model-agnosticism.md) et la [liste des adaptateurs](adapters/README.md).

## Verification

Run `python scripts/validate_team.py`, `python scripts/check_markdown_links.py`, `python scripts/check_cross_references.py`, `python scripts/check_placeholders.py` and `python -m unittest discover -s tests -v` locally, then inspect the actual CI result on the pull request. Use `docs/verification-report.md` to record a real Claude Code smoke test; do not mark runtime verification complete without evidence.

## Permissions mécaniques

Write scopes are centralized in `.claude/agent-scopes.json`. Before writing, run this fail-closed check:

```bash
python scripts/enforce_agent_scope.py --agent backend-developer --path src/backend/app.py
```

Exit code `0` allows the path, `1` denies it, and `2` indicates a usage error (for instance, an empty path). An agent missing from the configuration is denied. This preflight does not replace a sandbox or operating-system permissions that actually prevent unauthorized writes.

## Résolution de conflits <!-- codespell:ignore -->

The conflict protocol defines this authority order: **human sponsor > CP1–CP4 checkpoints > `software-architect` for architecture > `tech-lead` for code decisions > other agents**. After two unsuccessful rounds on the same story and topic, the orchestrator escalates to the human sponsor at the applicable checkpoint and blocks the affected transition until the human decision is recorded.

Before every transition, run the read-only detector:

```bash
python scripts/detect_conflict.py --story US-123 --agents software-architect,tech-lead
```

- Exit code `0`: no conflict exists for the story, or all matching records have a valid human decision.
- Exit code `1`: an unresolved conflict exists; stop and escalate.
- Exit code `2`: invalid arguments, an unreadable record, or malformed JSON; stop (fail closed).

Records live at `.claude/disagreements/<story>-<topic>.md`. Each file must contain a valid JSON object with both positions, blocking points, `human_decision`, and the date. See [`standards/conflict-resolution.md`](standards/conflict-resolution.md) for the full schema and rules.

## How to read state/effective.json

Generate a point-in-time reconciliation with `python scripts/status_snapshot.py`; use `--dry-run` to print JSON without writing, and `--output PATH` to choose another output path. The file contains `schema_version`, `generated_at`, `agents`, and `tasks`. Each agent reports declared and observed status, whether reliable evidence indicates drift, the age of the latest telemetry event, and staleness. `FRESH` means less than 15 minutes old, `STALE` means 15 minutes through 24 hours, and `UNKNOWN` means no usable event or an event older than 24 hours. `UNKNOWN` does not mean failed. Each task includes declared/observed status, drift, and evidence. GitHub issue/PR observations are included only when the optional `gh` CLI is installed and its queries succeed; otherwise the script warns and continues. Treat declarations as context, not proof, and inspect evidence before acting. See `docs/effective-schema.md` for field definitions.
