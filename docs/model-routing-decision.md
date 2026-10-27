# Agent Model Routing Policy

## Decision status

**Status: ADOPTED 2026-10-27, statically verified; runtime smoke test pending (see "Verification").**

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

No `model` field is set on skills or commands.

- The skills in `.claude/skills/` are procedural references. Agents read their `SKILL.md` before specialist work (see the skill routing table in `.claude/CLAUDE.md`). A `model` field has no effect when a file is read, and when a skill is invoked it would switch the model of the calling agent mid-task, overriding the routing above.
- The commands in `.claude/commands/` run in the orchestrator's session and delegate to agents. Those agents' own `model` fields already apply.

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
- [ ] Runtime smoke test: in a **new** session started after these frontmatter changes, delegate one trivial task each to `ci-verifier` (haiku) and `software-architect` (opus) and confirm in `/usage` or the transcript that the expected model ran. Record the result in `docs/verification-report.md`
  - 2026-10-27, attempt 1: **inconclusive.** It ran in the same session that edited the frontmatter. Claude Code loads agent definitions at session start, so both agents inherited the session model (`claude-opus-5-5` in both transcripts). Repeat it in a fresh session.
- [ ] Pilot sprint (#45): compare rework, review findings and usage per story; revisit tiers at sprint review

This record is not proof that runtime routing has been tested until the smoke-test box is checked with evidence.
