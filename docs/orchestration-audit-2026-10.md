# Orchestration and Agile workflow audit (2026-10-23)

- Scope: this repository at `e890c4f` (origin/main), and `ibrahim-ai-team/api-quiz-app` as the case study (main at `6698128`, issues, PRs and Actions runs read through the GitHub API on 2026-10-23).
- Method: file inspection, the repository's validators and unit tests, GitHub reads, and an offline run of the new checker against the real API Quiz files.
- Not verified: Claude Code runtime discovery and delegation in a fresh session; GitHub rulesets and branch protection (no admin read); GitHub Projects (none exists for API Quiz). Coordinator ledger entries cited below come from the local, gitignored `.provisioning/` file of this session; they are not in any repository.
- Labels: **Verified** = observed in a file, GitHub record or command output. **Assessment** = the auditor's reading of verified facts.

## 1. Lifecycle trace (Idea to merge)

| Transition | Where it is defined | Classification before this change | Evidence |
| --- | --- | --- | --- |
| Idea → requirements | `workflows/project-bootstrap.md`, `/kickoff`, `product-owner`, `business-analyst` | Documented; exercised once (API Quiz brief, `docs/planning/01-product-brief.md`) | Verified: brief exists in the app |
| Requirements → architecture | orchestration contract `ARCHITECTURE`, `software-architect` | Documented; exercised once (`03-architecture-adr.md`) | Verified |
| Architecture → backlog | `/provision-project`, `scripts/provision_project.py` | Implemented (script with tests; idempotent issue keys) | Verified: `tests/test_provision_project.py`; API Quiz issues carry `ai-team-key` markers |
| Backlog → sprint planning | `/plan-sprint`, `sprint-plan-template.md`, `agile-planning`, `sprint-execution-checklist.md`, `agile-agent-delivery.md` | Documented, duplicated in four places, no record format that names committed issues | Verified: template had only `TBD` fields; 0 milestones and no Project for API Quiz |
| Sprint scope during the sprint | — | Missing (no scope-change procedure) | Verified: no scope-change record exists |
| Implementation | `standards/agent-contract.md`, `check_claims.py` | Implemented for claims (script + tests); rest documented | Verified |
| Testing | `qa-automation`, `backlog-quality-gates.md` | Documented; app CI enforces tests | Verified: app CI runs |
| Code review | `tech-lead`, `code-review-security` (read-only tools) | Implemented as tool restriction; independence is policy | Verified: frontmatter `tools: Read, Grep, Glob` |
| PR → human merge | `.claude/settings.json` deny `gh pr merge*`, CLAUDE.md | Implemented as a local deny rule; GitHub enforcement not verified | Verified rule; rulesets not readable |
| Sprint closure / next sprint | `sprint-execution-checklist.md` ("Record carryover") | Missing as a rule: no closure criteria, no ban on extension, no replanning step | Verified |
| Release decision | `/release-check`, `release-manager` | Documented; no single home for thresholds; overrides not addressed | Verified |
| Conflicting requirements | contract precedence list | Contradictory/incomplete: precedence covered facts, not business decisions | Verified |

## 2. Findings

Severity scale: Critical, High, Medium, Low, Informational.

### F-01 Release criteria conflict, and the release ran through a bypass. Critical

- Evidence (Verified):
  - App `scripts/content/rules.ts:176-183` sets `minReviewedQuestions: 60, minTopics: 8`.
  - The 60/8 figure is repeated in `docs/planning/01-product-brief.md` (SC-2, line 31; line 85), in `05-backlog-sprint-plan.md`, in `docs/project-plan.json` and in issue #13 ("at least 60").
  - The current human decision given to this audit is 24 reviewed questions across 3 topics. It is not recorded anywhere in the app repository.
  - `.github/workflows/deploy-pages.yml:20` defines `accept_below_release_thresholds`. Deploy runs 39847942745, 39916746207 and 39922278097 published with it (the ledger records "SD-DEPLOY-01" as a chat decision).
  - The offline checker, run on the real files (§4), reports 4 mismatches and 2 bypass lines.
- Root cause: thresholds had no single authoritative home or decision ID. The kit had no rule for a newer decision versus an older requirement. Release override inputs were not prohibited.
- Impact: agents read different targets (60 in code, 24 from the sponsor). Releases pass by override rather than by criteria, so "release-ready" means nothing verifiable.
- Correction: one `## Release criteria` table with decision IDs and mirrors, plus a `## Requirement conflicts` table (`templates/project-state-template.md`). Precedence now puts human decisions above requirements and code (`workflows/orchestration-contract.md#authority-and-precedence`). `check_governance.py --release` fails on mismatches, open conflicts and bypass inputs.
- Validation: `tests/test_governance.py` `test_3_*`, and the live offline run in §4.
- App follow-up (not done here; the mission forbids app changes): the sponsor records the 24/3 decision. Then a reviewed app PR aligns `RELEASE_THRESHOLDS` and the docs, moves 60/8 to a future milestone, and removes the override input.

### F-02 Sprints are not tracked in a verifiable form. High

- Evidence (Verified):
  - API Quiz has 0 milestones, no Project, and no sprint label or field.
  - Sprint 2 dates in `06-sprint1-review-retro-sprint2-plan.md` §3.1 are "nominal 2026-11-09 to 2026-11-22", while Sprint 2 work was merged 2026-10-21/22.
  - "Sprint 3" was started by the coordinator on 2026-10-23 in the local ledger, with no plan file, dates or approval record.
- Root cause: `sprint-plan-template.md` held only `TBD` fields and no committed-issue list. No rule required real dates or approval, or said where membership lives.
- Impact: nobody can tell from GitHub which issues are in the sprint or when it ends. Reports about sprint progress cannot be checked.
- Correction: `workflows/sprint-governance.md` (where sprint facts live, ID/dates/goal/approval/capacity). A structured sprint record template. Checker rules G01–G06 and G15.
- Validation: `SprintRecordTests`; `test_7_*`.

### F-03 Issues created without recorded justification or duplicate search. High

- Evidence (Verified):
  - #88 (T-36) was created with no labels and no issue form, and without the template fields.
  - #100–#110 (T-37–T-47) were created in one batch from a tech-lead breakdown, with no duplicate-search record. #105–#108 overlap story #12 (US-6), which already holds those acceptance criteria. Assessment: they are legitimate subtasks, but they are not linked as sub-issues.
  - Issue forms had no duplicate-check or target field. `backlog-quality-gates.md` had no creation gate.
- Root cause: rules covered readiness, not creation. Forms could be bypassed by API creation.
- Impact: the backlog grows (37 → 47 tasks during Sprints 2–3) while MVP stories stay open, and justification is lost.
- Correction: `workflows/backlog-quality-gates.md#issue-creation-gate` (7 questions, reject conditions, exceptions, proportionality). `duplicate_check` and `target` fields in all four forms. The issue creation log in the sprint record. Checker rule G12.
- Validation: `test_1_duplicate_issue_is_rejected`, `test_2_*`.

### F-04 Scope changed during sprints without a record. High

- Evidence (Verified):
  - The ledger shows US-5 re-estimated 2→6 and US-6 5→14 (S3-TL01) with no approval.
  - Sponsor PR #86 (header) was merged outside any plan.
  - #45 (T-27) was closed by its PR although the OAuth/JWT part was cut (sponsor choice "HTTP auth only", made in chat).
- Root cause: no scope-change procedure, no capacity check, and no rule on closing issues whose scope was cut.
- Impact: a sprint's commitment silently grows or shrinks; cut scope disappears.
- Correction: `workflows/sprint-governance.md#scope-protection` (scope change row, what it displaces, approver). Capacity check G15. Closure rule 5 on cut scope.
- Validation: `test_2b_*`, `SprintRecordTests.test_capacity_is_enforced`.

### F-05 Story issues never accepted or closed; Done is not reconciled. High

- Evidence (Verified): stories #9, #10, #13, #14, #15 (P0) and #11, #12, #17 (P1) are open on 2026-10-23, although most of their tasks have merged PRs (e.g. #11 US-5 via #111–#113, #115). Assessment: no acceptance step closed them.
- Root cause: the DoD and status transitions covered tasks and PRs; nothing required story acceptance at sprint review.
- Impact: GitHub shows the MVP as not started, which hides real progress and real gaps alike.
- Correction: sprint closure rules 2–5 (final status per committed issue, story issues close on recorded acceptance). Checker G08 and G11.
- Validation: `test_4_*`, `test_6_*`.

### F-06 No sprint closure, carry-over or next-sprint rule. High

- Evidence (Verified): `sprint-execution-checklist.md` said only "Record carryover with reason and owner". There was no end-date rule, no replanning, and no closure states.
- Root cause: closure was never specified.
- Impact: sprints run until work ends (the Sprint 2 "end" was never recorded); everything unfinished rolls forward by default.
- Correction: `workflows/sprint-governance.md#sprint-closure` and `#next-sprint`. Checker G10, G11 and G14.
- Validation: `test_5_*`, `test_6_*`, `test_7_*`.

### F-07 Precedence did not cover business decisions. High

- Evidence (Verified): the old contract precedence ranked repository facts, sponsor decisions/ADRs, task status, delegation records, then chat. It had no ranking for release criteria, sprint commitment versus requirements, and no conflict procedure.
- Root cause: precedence was designed for fact reconciliation only.
- Impact: agents resolve conflicts by whichever source they read; see F-01.
- Correction: a 7-level authority order and conflict rules (`workflows/orchestration-contract.md#authority-and-precedence`); decision authority table (`standards/agent-contract.md#decision-authority`).
- Validation: text review; `test_3_*` exercises the conflict path.

### F-08 Coordinator ledger is local only. Medium

- Evidence (Verified): `.gitignore:24` ignores `.provisioning/`. API Quiz sprint state lived in `.provisioning/api-quiz/sprint1-state.md`, which is not in either repository.
- Root cause: the provisioning state file was reused as the sprint ledger.
- Impact: another session or person cannot resume from it; "durable state" is not durable.
- Correction: sprint records are committed to the project repository (`sprint-governance.md`, "A local, gitignored ledger is not project state").
- Validation: process; not machine-checked.

### F-09 Duplicated sprint rules across commands, skill, checklist and docs. Medium

- Evidence (Verified): sprint sizing and approval wording repeated in `/plan-sprint`, `agile-planning`, `agile-agent-delivery.md`, `github-projects-setup.md` and the checklist. There were contradictions on approval, resolved earlier as `docs/vision-alignment-audit.md` A3.
- Root cause: each artifact restated rules instead of linking.
- Correction: one authority (`sprint-governance.md`). `/plan-sprint`, `/sprint-review`, the checklist, `agile-planning` and `github-projects-setup.md` now link to it. Approval keeps A3's intent: the sponsor is not asked for routine sprints when a standing delegation to the Product Owner is recorded.
- Validation: `validate_team.py`, link and cross-reference checks.

### F-10 Skills had no input contract. Medium

- Evidence (Verified): all 23 skills had the same four sections (When to use, Procedure, Expected outputs, Quality checks) and no required inputs.
- Correction: a `## Required inputs` section in every skill with "stop and ask if missing". `validate_team.py` now requires all five sections. No skills or agents were added.
- Validation: `validate_team.py` PASS.

### F-11 Orchestrator did not reference the agent contract; no decision-authority matrix. Medium

- Evidence (Verified): `grep -L agent-contract .claude/agents/*.md` returned only `agile-orchestrator.md`. No file said who decides scope, release go/no-go or scope changes.
- Correction: the orchestrator links the contract, sprint governance and the decision table. The orchestrator is named as the only GitHub operator (no new "GitHub agent").
- Validation: text review.

### F-12 Release decisions could rely on overrides. Medium

- Evidence (Verified): see F-01. `/release-check` and `release-management` did not mention overrides or a criteria source.
- Correction: `/release-check`, the `release-manager` agent and the skill run `check_governance.py --release`; an override is a NO-GO.
- Validation: `test_3_release_bypass_input_blocks_release`.

### F-13 Completion could be claimed from an open PR. Low

- Evidence (Verified): `project-status-transitions.md` already forbids Done without a human merge. The sprint template had no evidence columns, so the rule could not be checked in a sprint record.
- Correction: Done rows need a PR reference and evidence containing "merged" (G08).
- Validation: `test_4_*`.

### F-14 Delegation verification works for code, not for state transitions. Informational

- Evidence (Verified): in this session every agent result was reconciled against PR diffs and CI before being reported (e.g. PR #99's failing test was found in CI and fixed in 3dd3834). But no issue state or board transition was read back, because no Project exists.
- Correction: none beyond F-02 and F-05; status read-back remains as specified in `project-status-transitions.md` once a Project is configured.

## 3. What the checker does and does not prove

`scripts/check_governance.py` is an offline consistency check of committed records, CI-run through the unit tests. It does not query GitHub. A passing run proves the record is complete and internally consistent, not that GitHub matches it. Reconciliation with GitHub remains the coordinator's job.

## 4. Offline run against the real API Quiz files

Input: a scratch project state stating the 24/3 decision, with mirrors to the real `scripts/content/rules.ts` and `docs/planning/01-product-brief.md` at app `6698128`. This is a real run on real files; the state record itself is a test input, not an app change.

- Normal mode: exit 1, four `G21 ... unrecorded requirement conflict` errors (24 vs 60, 3 vs 8, in code and brief).
- `--release`: exit 1, the same four plus `G22 release bypass` at `deploy-pages.yml:20` (input) and `:69` (its environment variable).

Assessment: the current bank (66 reviewed, 8 topics, PR #99) meets both 24/3 and 60/8. So the release is blocked by unrecorded and conflicting criteria and by the override input, not by content.
