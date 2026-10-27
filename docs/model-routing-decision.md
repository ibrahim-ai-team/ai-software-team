# Agent Model Routing Policy

## Decision status

**Status: ADOPTED 2026-10-27; routing verified at runtime (see "Verification").**

Supersedes the DEFERRED decision of PR #44. Each specialist now declares a Claude Code `model` alias in its frontmatter. `agile-orchestrator` declares none, so the main session keeps the model the sponsor picks with `/model`.

## Runtime and account facts

| Fact | Value | Evidence |
| --- | --- | --- |
| Claude Code version | 2.1.312 | `~/.local/bin/claude` → `~/.local/share/claude/versions/2.1.312` |
| Model IDs known to that binary | `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5` | String search of the installed binary |
| Frontmatter syntax | `model: sonnet \| opus \| haiku \| fable \| inherit` or a full `claude-*` ID; omitted = `inherit` | code.claude.com/docs/en/sub-agents (checked 2026-10-19); enforced by `scripts/check_cross_references.py` |
| Account | Claude Pro (`standards/sprint-sizing.md`); usage limits, not dollars | Sprint-sizing standard |
| Relative API price (input/output per MTok) | Fable 5.1 $10/$50 · Opus 5.5 $4/$20 · Sonnet 5.5 $2/$10 · Haiku 5.5 $0.10/$0.50 | Anthropic model table cached 2026-10-06. On Pro, usage is not billed per token, but heavier models use up the five-hour and weekly limits faster |

Aliases are used instead of full IDs. An alias follows the newest model in its family, so the kit needs no edit when a model is replaced. Re-check this file when an alias changes meaning.

## Assignments

| Tier | Agents | Why |
| --- | --- | --- |
| *(unset, inherits session)* | `agile-orchestrator` | Main session started with `--agent`; it runs every turn, so the sponsor controls its cost with `/model`. Pinning it would override that choice |
| `opus` | `software-architect` | Architecture trade-offs and ADRs are hard to reverse and drive all later work. Runs rarely (once per project or epic, 25-turn cap), so the extra usage is small |
| `opus` | `code-review-security` | Independent read-only security gate. A missed vulnerability costs far more than the review does. Read-only, so the stronger model adds no write risk |
| `sonnet` | `backend-developer`, `frontend-developer`, `database-engineer`, `devops-platform`, `qa-automation` | Implementation and tests within a Tech Lead breakdown, checked by tests, `tech-lead`, `code-review-security` and CI. These are the longest delegations (60 turns), so this tier decides most of a sprint's usage |
| `sonnet` | `tech-lead` | Breakdown and technical review within an approved architecture. The security and correctness second look is already on `opus`; keeping this review on `sonnet` holds a story's two reviews to one premium delegation |
| `sonnet` | `product-owner`, `business-analyst`, `project-manager`, `ui-ux-designer`, `documentation-manager`, `technical-research` | Structured planning, writing and research with templates and quality gates. The sponsor and the Definition of Ready catch gaps |
| `sonnet` | `performance-engineer`, `sre-observability-engineer`, `release-manager` | Measurement and evidence work. The decisions rest on observed data and the human go/no-go, not on the model's judgement alone |
| `haiku` | `ci-verifier` | Runs only allowlisted commands and reports observed output as JSON; it never fixes anything. `code-review-security` independently judges whether the evidence supports G2 |
| `haiku` | `github-integration` | Carries out operations the orchestrator has already decided (Issues, PRs, board). Makes no planning or priority choices; provisioning is idempotent and destructive `gh` actions are denied in `.claude/settings.json` |

`fable` is not assigned. It costs about 2.5 times as much as Opus. Its availability on the Pro plan has not been verified, and no role needs more than Opus can give.

### Effect when the session runs on the default model

If the main session runs on Sonnet, most delegations behave as before. Two roles move up (`software-architect`, `code-review-security`) and two move down (`ci-verifier`, `github-integration`). If the sponsor switches the session to Opus, delegations no longer all follow it to Opus: implementation stays on Sonnet. That is the main saving.

## Skills and commands

Skills are routed by complexity **per delegation**, not by a `model` field in `SKILL.md`.

- **Why not a skill `model` field:** no agent has the `Skill` tool or a `skills:` preload. Every agent reads `.claude/skills/<name>/SKILL.md` as a file, and a skill `model` field applies only when a skill is *invoked*. It would only act when the sponsor types `/<skill-name>` in the main session, where it would silently override `/model`.
- **What works instead:** the delegation itself can set a model, and that overrides the agent's frontmatter for that one delegation (documented on the Claude Code 2.1.312 `Agent` tool: "Takes precedence over the agent definition's model frontmatter"). The orchestrator therefore picks a tier for each delegation from the complexity of the skill the task needs.
- The commands in `.claude/commands/` run in the orchestrator's session and delegate to agents, so the same routing applies.

### Tiers

| Tier | Claude Code alias | Use for |
| --- | --- | --- |
| light | `haiku` | Procedural work with a fixed checklist or command set; output verified by someone else |
| standard | `sonnet` | Judgement within an approved design: implementation, tests, planning, structured writing |
| premium | `opus` | Hard-to-reverse decisions and adversarial reasoning: architecture, stack choice, security |

`fable` is never selected by routing. Using it is a sponsor decision (cost and Pro availability).

### Complexity tier per skill

| Skill | Tier | Why |
| --- | --- | --- |
| `git-github-workflows` | light | Fixed branch/commit/PR procedure; protected by hooks and deny rules |
| `token-context-cost-management` | light | Checklist of budgeting rules |
| `documentation-session-handover` | light | Fills a template from evidence the orchestrator has already reconciled |
| `agile-planning` | standard | Sequencing and capacity trade-offs |
| `requirements-analysis` | standard | Turning ambiguity into testable scope; the sponsor and Definition of Ready check it |
| `user-stories-acceptance-criteria` | standard | Small stories with testable criteria |
| `ui-ux-design-system` | standard | Flows and patterns within product scope |
| `accessibility-review` | standard | Checklist-driven, but needs judgement on semantics and focus |
| `frontend-engineering-standards` | standard | Production code, checked by tests and two reviews |
| `backend-engineering-standards` | standard | Production code, checked by tests and two reviews |
| `api-design-documentation` | standard | Contract design within the architecture |
| `database-modelling-migrations` | standard | Schema work; raised for existing-data migrations (rule 2) |
| `test-strategy-automation` | standard | Risk-based test design and code |
| `debugging-root-cause-analysis` | standard | Most defects reproduce simply; raised after a failed attempt (rule 2) |
| `code-review-refactoring` | standard | Review against standards; the security pass is separate |
| `docker-cicd` | standard | Pipeline and container changes, verified by CI |
| `observability-sre` | standard | SLOs, telemetry and runbooks from measured data |
| `performance-testing` | standard | Measurement design; conclusions rest on data |
| `release-management` | standard | Evidence collection; the human makes the go/no-go |
| `technical-research-source-verification` | standard | Source checking and synthesis |
| `architecture-evaluation-adr` | premium | Hard-to-reverse trade-offs that drive all later work |
| `technology-stack-selection` | premium | Long-lived, costly-to-change choice |
| `security-threat-modelling` | premium | Adversarial reasoning; a miss is expensive |

### Resolving a delegation's tier

1. **Base:** the tier of the task's primary skill, meaning the first skill named in the brief.
2. **Raise one tier** (at most premium, once per delegation) if any of these applies: size L (5 points); the change touches authentication, authorization, payments, personal data, secrets, or migrates existing data; or the previous attempt at the same task failed or hit its turn cap.
3. **Lower one tier** (at least light) only if the size is XS (1 point), the base is standard, no raise applies, and the task changes no production code or tests (docs, configuration copy, board or issue updates, report formatting).
4. **Clamp to the agent's bounds:**

   | Agent | Allowed tiers |
   | --- | --- |
   | `software-architect`, `code-review-security` | premium only. Gates are never downgraded |
   | `ci-verifier`, `github-integration` | light only. Mechanical execution |
   | `backend-developer`, `frontend-developer`, `database-engineer`, `devops-platform`, `qa-automation`, `performance-engineer`, `tech-lead` | standard–premium. They write or review production code and tests |
   | All other specialists | light–premium |

5. **Apply:** if the result equals the agent's frontmatter default (Assignments above), set nothing. Otherwise set the tier's alias on that delegation only. Record the tier, and the rule that changed it, in the delegation record (`templates/agent-delegation-template.md`).

Examples: an XS README fix by `documentation-manager` goes to light. An M feature in `backend-developer` touching authorization goes to premium. A first diagnosis by `qa-automation` stays standard; if it fails, the retry goes to premium. Any review by `code-review-security` stays premium.

The frontmatter defaults remain the fallback when the orchestrator sets nothing. This routing changes cost, not role responsibilities, tools, turn caps or gates.

## Policy

1. Prefer the least expensive model that reliably meets the role's quality and safety needs.
2. Reserve `opus` for architecture trade-offs, security-sensitive review, and complex debugging or ambiguous requirements when observed results justify it.
3. Do not pin the orchestrator, and do not route every agent to a premium model.
4. Change a tier only with evidence (a defect escape, rework, a cap hit, or a usage problem) recorded in the sprint review. Update this table in the same pull request.
5. Keep credentials and billing details out of committed files. Never set `ANTHROPIC_API_KEY` (`standards/sprint-sizing.md`).

## Fallback

If an alias is not available on the account, the delegation fails with a model error. The orchestrator records the failure, then either changes that agent's `model` to `sonnet` in a pull request or asks the sponsor. It does not retry the same delegation.

## Model agnosticism

`model` is a Claude Code runtime field, documented here as the adapter detail allowed by `standards/model-agnosticism.md`. It does not change any role's responsibilities, tools, turn cap, gates or evidence. Another runtime may ignore it or map the tiers (premium, standard, light) to its own models.

## Verification

- [x] Supported syntax and aliases confirmed (official docs, validator, binary 2.1.312)
- [x] Installed version and account constraints recorded
- [x] Runtime smoke test: in a **new** session started after these frontmatter changes, delegate one trivial task each to `ci-verifier` (haiku) and `software-architect` (opus) and confirm in `/usage` or the transcript that the expected model ran. Record the result in `docs/verification-report.md`
  - 2026-10-27, attempt 1: **inconclusive.** It ran in the same session that edited the frontmatter. Claude Code loads agent definitions at session start, so both agents inherited the session model (`claude-opus-5-5` in both transcripts). Repeat it in a fresh session.
  - 2026-10-27, attempt 2 (fresh `claude --agent agile-orchestrator` session, Claude Code 2.1.312, branch `chore/agent-model-routing` at `f473b77`): **passed.** SMOKE-MODEL-05 `ci-verifier` ran every turn on `claude-haiku-5-5`. SMOKE-MODEL-06 `software-architect` ran every turn on `claude-opus-5-5`. The one `claude-opus-5-5` value in the ci-verifier transcript is the model of the built-in `advisor` tool (deferred, not called), not a turn the agent ran. Evidence: the subagent transcripts' `model` fields. This shows routing only, not application behaviour.
- [x] Per-delegation override: 2026-10-27, SMOKE-MODEL-07 delegated to `documentation-manager` (default `sonnet`) with a `haiku` override. Every turn ran on `claude-haiku-5-5` per the transcript `model` fields; the one `claude-opus-5-5` value is the `advisor` tool definition. This confirms the mechanism behind "Resolving a delegation's tier".
- [ ] Pilot sprint (#45): compare rework, review findings and usage per story; revisit tiers at sprint review

The smoke test verified two agents, one each on `haiku` and `opus`. The `sonnet` agents use the same frontmatter mechanism but were not run individually.
