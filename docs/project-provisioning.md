# Project provisioning

`/provision-project` turns an approved project plan into an independent GitHub workspace in the `ibrahim-ai-team` organization. The engine is `scripts/provision_project.py`; the plan format is `templates/project-plan.example.json`.

`ai-software-team` stays the reusable team. Generated repositories get their own README, contribution and security files, but not a copy of the agents, skills or workflows. They link back to this repository through the orchestrator, which runs from here.

## Status of this feature

| Area | State |
|---|---|
| Planning, validation, repository tree, naming | Implemented and unit-tested (mocked GitHub) |
| Provisioning engine: idempotency, retries, partial failure, permission reporting | Implemented and unit-tested (mocked GitHub) |
| Real GitHub calls (`GhClient`) | Read paths verified against the real API (PV-02); error classification tested with recorded `gh` outputs (mocked). Write paths (create repositories, files, PRs, issues, board, iteration field) **NOT VERIFIED**; no real repositories were created during development |
| End-to-end on the real organization | **NOT RUN**. The feature is not "fully automated" until an authorized real run is recorded in `docs/verification-report.md` |

## Naming and the "apps" grouping

GitHub repositories cannot be nested in folders. The "apps" grouping is therefore expressed with:

- **Name prefix:** every project gets a unique ID `idea-NN`, and its repositories are `idea-NN-<role>`. The next free ID is computed from existing `idea-NN-*` repositories.
- **Topics:** `ai-team-app`, the project ID (for example `idea-01`) and the role, on every repository.
- **Description tag:** `[ai-team:idea-NN]`, used to tell this project's repositories from unrelated ones.
- **One GitHub Project board per idea:** titled `idea-NN · <Name>`, linked to all of the project's repositories.
- **One label per idea:** `project:idea-NN` on every issue, plus a hidden key comment (`ai-team-key: idea-NN/US-1`) in the body.

Roles depend on the architecture the team chose:

| `architecture.style` | Repositories |
|---|---|
| single-repo, monolith | `idea-NN-app` (coordination docs live in its `docs/`) |
| frontend-backend | `idea-NN-management`, `idea-NN-front`, `idea-NN-back` |
| services | `idea-NN-management`, optional `idea-NN-front`, one `idea-NN-<service>` per service |

`coordination_repo` defaults to `auto`: a coordination repository `idea-NN-management` is created when there is more than one repository. Set it to `true` or `false` to override. Explicit `repositories` entries replace the defaults. Every application repository must declare `purpose`, `stack` and `testing` before it can be created, matching the creation gate in `docs/workspace-architecture.md`.

## What one run creates

For each repository:
- the repository (private by default) with an initial commit;
- topics, labels and one `idea-NN Sprint n` milestone per sprint (14 days by default);
- a bootstrap/initial-structure branch with README, CONTRIBUTING, SECURITY, CODEOWNERS and a PR template, plus an open bootstrap PR for the owner to merge;
- in the coordination repository only: requirements, ADR-0001, the repository plan, the approved plan, `docs/project-state.md` and `docs/provisioning-report.md`.

Across the project:
- one issue per backlog item in the repository it belongs to, with acceptance criteria, priority, sprint milestone and cross-repository dependency links;
- the Project board, with the repositories linked, all issues added and an iteration field "Sprint".

Branch protection is applied only when the approved plan sets `options.branch_protection: true`. Otherwise it is listed as a manual action.

## Approval

`apply` refuses to run unless `approval.plan_digest` equals the digest printed by `plan`. The digest covers the whole normalized plan except the approval block. Changing anything (a repository, visibility, the backlog) requires a new approval. `--dry-run` needs no approval and writes nothing.

`.claude/settings.json` also asks a human before any command containing `provision_project.py apply` runs (verified at runtime: PV-05).

**What these gates do not guarantee:**
- The digest is self-attested: an agent could write it into the plan.
- The ask rule is a text pattern: an agent could avoid it (for example by calling the module from `python -c`).
- Agents act with the same GitHub identity as the owner, so GitHub cannot tell an agent's request from the owner's.

The gates are therefore instruction- and prompt-based safeguards, not enforced isolation. Separating them for real would need provisioning credentials the agent does not have, for example running `apply` yourself in your own terminal.

## States, retries and recovery

Each step is recorded in `.provisioning/<idea-NN>.json` (git-ignored, local) and summarised in the coordination repository's `docs/provisioning-report.md`.

| Step status | Meaning | What to do |
|---|---|---|
| `CREATED` / `UPDATED` | Done in this run | — |
| `EXISTS` | Already present; nothing written | — |
| `DRY_RUN` | Would be created; nothing written | — |
| `PERMISSION_DENIED` | GitHub returned 401/403; the detail names the permission needed | Grant it, then rerun |
| `FAILED` | Error after retries, or an unexpected exception (recorded, not crashing the run) | Fix the cause, then rerun |
| `SKIPPED_DEPENDENCY` | A prerequisite step did not succeed, or a dependency issue does not exist yet | Rerun after the prerequisite succeeds |

Transient errors are retried twice, after 5 s and then 20 s: HTTP 429, 5xx, network failures, GitHub's secondary rate limit (reported as 403), and a just-created repository whose first commit is not visible yet. Other errors are not retried. GraphQL errors are classified by their type (`FORBIDDEN` and `INSUFFICIENT_SCOPES` are permission errors). A failed repository skips only the steps that depend on it; independent work continues.

Overall phases:
- `COMPLETE`, or `COMPLETE_WITH_MANUAL_STEPS`;
- `PARTIAL`: some step needs action;
- `BLOCKED`: a repository with the planned name exists but has no `[ai-team:idea-NN]` tag. Nothing is changed; choose another ID.

Reruns are idempotent. Repositories, labels, milestones, the branch, the PR, issues (found by their key) and the board are reused; the provisioning report is rewritten only when its content changed, and never to a closed bootstrap PR. Boards are adopted only if their description carries `[ai-team:idea-NN]`; a same-titled board without it fails the project step.

**Known limits:**
- Issues are matched by the `project:idea-NN` label plus the hidden key. Removing that label from an issue would make a rerun create a duplicate.
- Board lookups read the first 100 items and 50 repositories or fields; re-adding an existing item is harmless.
- Recorded error text is truncated and token-like strings are redacted, but it is still committed in the report; keep repositories private when errors may contain sensitive context.

## Permissions required

Run provisioning from a local Claude Code session where `gh auth login` was done as an organization owner (or a member allowed to create repositories). Cloud sessions can only reach their configured repositories, so they cannot create repositories or organization boards.

| Operation | Permission |
|---|---|
| Read existing repositories | Read access to the organization's repositories |
| Create repositories | Organization owner, or members allowed to create repositories (Organization settings → Member privileges); token scope `repo`, or fine-grained Administration: write |
| Topics, branch protection | Repository Administration: write (admin role) |
| Bootstrap branch, files | Repository Contents: write |
| Bootstrap PR | Repository Pull requests: write |
| Labels, milestones, issues | Repository Issues: write |
| Project board | Organization Projects: read and write; token scope `project` (`gh auth refresh -s project`) |

## Manual steps after a run

- Merge each bootstrap PR (owner only).
- Align the board's Status options with `workflows/project-status-transitions.md`, and enable the Project workflows "Item closed → Done" and "Auto-add to project".
- Protect `main` in each new repository, unless the plan enabled it. Add CI checks as required once the repository has CI (a first-sprint task for `devops-platform`).
- Install the Claude GitHub App on the new repositories if cloud sessions should work on them.

## Example: one idea to a workspace

1. You say: "Build an e-commerce platform."
2. `agile-orchestrator` runs `/kickoff`.
   - `product-owner` and `business-analyst` write the requirements and stories.
   - `software-architect` chooses "frontend-backend" with a modular-monolith API, and writes the trade-offs as an ADR.
   - `tech-lead` confirms each repository's stack and tests.
   - `project-manager` sets a two-week sprint.
3. The orchestrator writes `.provisioning/idea-01-plan.json` (like `templates/project-plan.example.json`) and runs `plan --check-github`. That prints the repository tree, `idea-01-management` / `idea-01-front` / `idea-01-back`, and a digest.
4. You approve the tree and digest in one answer.
5. `apply --dry-run`, then `apply`, create:
   - the three repositories;
   - three bootstrap PRs;
   - four issues (an epic in management, an API story in back, a page story and an end-to-end QA task in front), with `US-2` linking to `US-1` across repositories;
   - `idea-01 Sprint 1` milestones;
   - the board `idea-01 · Shop Platform`.
6. You merge the bootstrap PRs. The orchestrator continues with `/plan-sprint` and `/next-story` in the new repositories.

## Testing

`tests/test_provision_project.py` runs the engine against an in-memory fake GitHub (mocked; no network). It covers:
- naming and next-ID assignment;
- the repository plans for each architecture style;
- validation errors and dependency cycles;
- a full run and an idempotent rerun;
- foreign-repository blocking;
- a missing Projects permission;
- partial failure with resume;
- transient retries;
- isolation between two ideas;
- branch protection only on approval;
- dry run with no writes;
- the approval digest gate.

A real integration test needs an authorized local session and a safe target, for example a throwaway `idea-99` project created and then deleted by the owner. Record its result as a runtime entry in `docs/verification-report.md`.
