# Changelog

Notable changes to this starter kit are recorded here.

## Unreleased

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
