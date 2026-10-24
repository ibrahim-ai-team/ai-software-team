# Changelog

Notable changes to this starter kit are recorded here.

## Unreleased

### Added

- Split GitHub execution into the bounded `github-integration` agent; reduced orchestrator responsibilities and added fail-safe, story-filtered lesson selection with regression tests and six targeted unit tests.

- Added the read-only `ci-verifier` role and schema tests; separated factual CI command execution from `code-review-security` G2 judgment, with orchestrator-only persistence after approval.

- Added fail-closed agent path-scope configuration, a standard-library preflight checker, regression tests, and documentation distinguishing preflight checks from runtime enforcement.

- Documented model-agnostic agent-contract principles, planned adapter interface, current Claude Code coupling, portability audit, and static guardrails against selected undocumented runtime syntax in agent Markdown. No agent files or adapter implementations were changed.

- Added a standard-library Python dependency license checker and push/PR workflow, license-risk and CI/CD hardening standards, minimal-permission workflow audit, validator coverage, security-policy links, and license-check tests.

- Added local sprint ROI reporting: JSON metrics input schema, standard-library Markdown report generator, sprint workflow/Project Manager instructions, worked calculation example, and regression tests.

- Agent worktree isolation policy, portable creation/cleanup scripts, and shell regression tests. Writing agents are instructed to work only inside their assigned per-story worktree and never write directly to `main`.

- Added: EARS specification template and SDD standard requiring validated story specs before G1, Product Owner/Business Analyst ownership, human CP1 and Software Architect review, format tests, bootstrap workflow guidance, and README documentation.
- Added: EARS specification template, SDD standard requiring a validated spec and human CP1 plus architect review before G1, agent/bootstrap instructions, and regression tests.
- Added: append-only persistent lessons with sequential IDs, conservative sensitive-term rejection, tests, and mandatory orchestrator/workflow instructions to read applicable lessons before delegation and record sanitized lessons after failed Gates.\n\n- Added: mechanical G1 plan-review and G2 post-execution validation gates, read-only gate checker, gate schemas/examples, orchestrator and delivery workflow enforcement, reviewer output contract, validator coverage, and regression tests.

- Added: mandatory human-in-the-loop checkpoints (CP1 plan, CP2 architecture, CP3 code before merge, CP4 release before tag), read-only approval-record validation, orchestrator enforcement instructions, validator coverage, and regression tests.

- Added: local append-only JSONL telemetry with UUID4 trace IDs, secret-key rejection, event analysis, orchestrator delegation/gate guidance, tests, and validator coverage.
- Added: pre-commit hooks (`.pre-commit-config.yaml`, `ruff.toml`, `.markdownlint-cli2.yaml`) for branch safety, secrets, Python lint and formatting, Markdown lint, spelling, file hygiene, GitHub workflow checks, the team's own checks and tests before push, plus a **Pre-commit hooks** CI workflow. Python files are reformatted, Markdown files normalized (blank lines around headings and lists, table separators) and scripts marked executable; no content changes.
- Changed: the operating model is Claude Pro only. `standards/sprint-sizing.md` v2 replaces dollar and API-equivalent budgets with sessions, delegations per session, enforced turn caps and usage-limit checkpoints (`/status`, `/usage`), and adds token-saving practices. One active delegation at a time by default; every session ends with a Project Manager report saved with the handover. Stack selection prefers free and open-source tools; the GitHub Actions free-minutes trade-off is documented. Never set `ANTHROPIC_API_KEY`.
- Added: `standards/sprint-sizing.md` (story points with a must-split rule, per-role turn caps, capacity formula; budgets later replaced by the Pro usage model above). Every specialist agent has an enforced `maxTurns` cap; the sprint plan, daily report and delegation templates carry size and budget fields (#26).
- Added: `/provision-project` and `scripts/provision_project.py`. They validate a team-produced project plan, print the repository tree, require the sponsor's approval of the plan digest, then idempotently create `<app>-<role>` repositories (for example `shopinow-front`; `idea-NN` stays the hidden project ID), bootstrap PRs, labels, sprint milestones, linked issues and a Project board, recording every step. Mocked tests only; the real GitHub path is not yet verified.
- Security: `tech-lead` is read-only (Read, Grep, Glob); the review-mode "do not edit" instruction is replaced by allowlist enforcement, and the validator rejects Edit/Write/Bash on it.
- Added: `agile-orchestrator` as the single entry point (`claude --agent agile-orchestrator`) and the only agent allowed to delegate; `tech-lead` for task breakdown, standards and technical review; `standards/agent-contract.md` with shared scope, return and evidence rules.
- Changed: agents get role-specific definition of done and escalation sections instead of repeated boilerplate; sprints default to two weeks and are reported rather than approved by the sponsor; Scrum Master and QA Engineer roles are named in their agents.
- Security: removed six `Write(path)` ask rules that Claude Code 2.1.303 never matches (each had an effective `Edit(path)` rule); the validator now rejects such rules.
- Fixed: the cross-reference check accepts documented model values and frontmatter keys and verifies the orchestrator names every required agent.
- Added: MIT License (#36).
- Security: deny GitHub MCP merge and auto-merge tools for agents (#24).
- Added: CI checks for command references, agent frontmatter, unresolved placeholders (#32, #43) and a pre-dispatch claim-conflict check with a documented claim/release/recovery protocol (#42).
- Changed: the Project status workflow targets a configurable Project, finds items from the issue side (no 100-item limit), supports `dry_run` and `add_if_missing`, and was verified by a real update and read-back (#40).
- Added: changelog/release convention, CODEOWNERS sensitive paths and an owner-unavailability rule (#39, #35); dated secret-scanning status (#34).
- Added: pilot readiness record, runtime verification report and pilot issue (#45).
- Add local Claude Code permission deny rules for selected dangerous commands and sensitive paths.
- Add a Gitleaks GitHub Actions workflow and common local-secret ignore patterns.
- Harden repository validation for required command/template inventories, non-empty content, and selected security configuration.
- Add negative validator regression tests for manifest containment, hard inventory floors, workflow permissions, action SHA pins, and command metadata.
- Compare manifest requirements with the pull-request base in CI to detect silent reductions.
- Extend Claude Code deny rules for destructive Git operations and repository deletion.
- Rename the mock discovery check to an offline inventory check and remove its duplicate frontmatter parser.
- Disable persisted checkout credentials in the validation workflow.
- Remove direct file-write capability from the technical research agent.
- Add sprint review, retrospective, and release-readiness commands and templates.
- Add weekly Dependabot updates for GitHub Actions.
- Add GitHub pull request template, CODEOWNERS, security policy, and contribution guidance.
- Harden Claude Code permission guardrails: close git-push flag/refspec gaps, add recursive-delete and credential-exposure denies, add `Edit` protections for secret files, add `ask` confirmation for settings, workflows, CODEOWNERS and risky `gh` commands.
- Validate `ask`/`allow` rule structure and add simulated rule-matching and validator negative tests (`tests/test_security_guardrails.py`); document limits in `docs/security-guardrails.md`.
