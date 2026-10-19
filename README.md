# AI Software Team

A reusable, project-independent starter kit for coordinating AI-assisted software delivery with Claude Code. It contains agent definitions, skills, engineering standards, templates, and workflows—not an application.

## What is included

| Area | Contents |
|---|---|
| Agents | 18 roles under `.claude/agents/`: one `agile-orchestrator` plus specialists (see [team roles](#team-roles)) |
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
3. Start the team from this directory with `claude --agent agile-orchestrator`. This makes the orchestrator the main session; it delegates to the specialists.
4. To check the setup only, ask it to report which agents and skills it discovers. To start a project, give it your idea (next section).

For a fictional end-to-end illustration, see [Example Walkthrough](docs/example-walkthrough.md). The example is documentation, not runtime evidence.

## Team roles

One orchestrator coordinates; specialists do the work and return results to it. Only the orchestrator can delegate.

| Role | Agent file |
|---|---|
| Agile Orchestrator (entry point) | `.claude/agents/agile-orchestrator.md` |
| Product Owner | `.claude/agents/product-owner.md` |
| Business Analyst | `.claude/agents/business-analyst.md` |
| Scrum Master / Project Manager | `.claude/agents/project-manager.md` |
| Architect | `.claude/agents/software-architect.md` |
| Tech Lead | `.claude/agents/tech-lead.md` |
| Frontend / Backend Developer | `.claude/agents/frontend-developer.md`, `.claude/agents/backend-developer.md` |
| QA Engineer | `.claude/agents/qa-automation.md` |
| DevOps Engineer | `.claude/agents/devops-platform.md` |
| Code / Security Reviewer | `.claude/agents/code-review-security.md` (read-only) |
| GitHub integration | `agile-orchestrator` (Issues, PRs, board status via `gh` and `.github/workflows/project-status.yml`) |
| Used when needed | `database-engineer`, `ui-ux-designer`, `technical-research`, `performance-engineer`, `sre-observability-engineer`, `release-manager`, `documentation-manager` |

Shared rules for every specialist: [`standards/agent-contract.md`](standards/agent-contract.md).

## Agile commands

A new idea becomes its own GitHub workspace named after the app you propose (for example `shopinow-management`, `shopinow-front`, `shopinow-back`) with one Project board through `/provision-project`; see [project provisioning](docs/project-provisioning.md). This repository is never copied per application.


The available prompts include `/kickoff`, `/provision-project`, `/plan-sprint`, `/next-story`, `/review-pr`, `/status`, `/daily-report`, `/handover`, `/approve-gate`, `/sprint-review`, `/retro`, and `/release-check`. See [the command reference](docs/agile-command-reference.md). Commands run only when invoked in Claude Code; they are not background jobs.

## Give the team an idea

When ready to start an application, describe it in plain language, for example: "Build an e-commerce website where customers can browse products, purchase items, and track orders."

The team should perform discovery, requirements, architecture options, backlog preparation, test strategy and delivery planning, then implement incrementally through bounded tasks, isolated branches and PRs. The user supervises progress and makes material sponsor decisions; the team owns routine planning and coordination. The human owner alone merges PRs.

For the exact phases, recovery rules, evidence requirements and safety boundaries, read `workflows/orchestration-contract.md`, then `workflows/project-bootstrap.md` and `workflows/agile-agent-delivery.md`.

## Important security limits

- `.claude/settings.json` defines client-side permission deny rules for selected dangerous commands and sensitive file paths. These are defense-in-depth, not a substitute for GitHub permissions, branch protection, or careful review. Test behavior in the installed Claude Code version.
- `.gitignore` reduces accidental tracking of common local secret files but cannot remove secrets already committed.
- Gitleaks runs in GitHub Actions; separately enable GitHub Secret Scanning and Push Protection where available.
- Configure and verify GitHub rulesets/branch protection and permissions separately. Do not treat the human-merge rule in documentation as technical enforcement.
- The validation workflow uses read-only repository permissions and disables persisted checkout credentials.

## Important limits

- This repository does not itself run a background agent team when Claude Code is closed.
- Markdown task records and GitHub labels are not atomic distributed locks. The documented protocol is single-coordinator/single-writer unless separate isolated worktrees and a real coordination mechanism are configured.
- The validator reads `.claude/manifest.json` for minimum agent/skill inventories and required command/template files. The offline `scripts/smoke_discovery.py` checks whether inventory files and agent/skill metadata can be discovered without launching Claude Code. Neither check proves real Claude Code discovery, delegation, application correctness, deployment, or branch protection.
- Licensed under the [MIT License](LICENSE): free to use, copy, modify and share, including in your own applications, provided the copyright notice is kept. Applications built with this kit choose their own licence.

## Verification

Run `python scripts/validate_team.py`, `python scripts/check_markdown_links.py`, `python scripts/check_cross_references.py`, `python scripts/check_placeholders.py` and `python -m unittest discover -s tests -v` locally, then inspect the actual CI result on the pull request. Use `docs/verification-report.md` to record a real Claude Code smoke test; do not mark runtime verification complete without evidence.
