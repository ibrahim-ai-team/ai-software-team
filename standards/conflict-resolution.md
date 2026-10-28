# Conflict Resolution

## Authority hierarchy

Resolve disagreements using this order, from highest to lowest:

1. **Human sponsor** — final decision-maker for material scope, business direction, risk acceptance and escalated disagreements.
2. **CP1–CP4 human checkpoints** — the applicable checkpoint approval is mandatory; an agent cannot substitute for or override it. A checkpoint decision governs the artifact and transition it approves.
3. **`software-architect`** — technical architecture decisions and ADRs, within approved scope and security constraints.
4. **`tech-lead`** — code-level decisions, implementation conventions and task-level technical choices, within the approved architecture and standards.
5. **All other agents** — provide evidence, proposals and role-specific findings; they cannot override higher authority.

Security requirements, repository protections, and applicable law remain hard constraints: no authority level may waive them through an ordinary technical decision. A human sponsor may explicitly decide a documented risk-acceptance question only where policy and law permit it.

Examples:

- If the Architect recommends microservices and the Tech Lead recommends a monolith, the Architect owns the architecture decision. The Tech Lead may record technical objections and implementation risks; if disagreement persists, apply the two-strike escalation below.
- If QA reports a reproducible acceptance-criteria bug and an implementer refuses to fix it, QA's evidence must be recorded and the orchestrator blocks completion; the implementer cannot veto verification findings. The Tech Lead may adjudicate implementation details, but cannot waive acceptance criteria.
- If `code-review-security` blocks a PR that the Tech Lead approved, the security finding remains blocking until resolved or formally dispositioned under applicable policy. Tech Lead approval does not override security review.

## Two-strike escalation

For the same topic and story, agents may attempt at most **two evidence-based rounds** to reconcile their positions. If the disagreement remains after the second round, the orchestrator must automatically escalate it to the human sponsor at the checkpoint relevant to the current lifecycle phase (CP1–CP4). Do not restart the count by renaming the topic or changing agents.

The orchestrator must:

1. Preserve both positions and supporting evidence.
2. Create/update `.claude/disagreements/<story>-<topic>.md`.
3. Identify the applicable checkpoint and ask the human sponsor for a decision.
4. Stop the affected transition and all work that depends on the disputed decision until the decision is recorded.

## Disagreement record format

Each record is a UTF-8 JSON object stored in a file ending in `.md` at `.claude/disagreements/<story>-<topic>.md`. The extension is retained for the repository's human-readable Markdown artifact convention; the file content **must be valid JSON** so the read-only detector can fail closed.

Required shape:

```json
{
  "story": "US-123",
  "topic": "architecture-choice",
  "agents": ["software-architect", "tech-lead"],
  "position_a": {
    "agent": "software-architect",
    "argument": "A modular monolith meets the MVP constraints with less operational overhead."
  },
  "position_b": {
    "agent": "tech-lead",
    "argument": "Independent services may isolate deployment and scaling."
  },
  "blocking_points": ["Deployment topology changes operational cost and ownership."],
  "human_decision": {
    "decided_by": "human sponsor",
    "decision": "Use a modular monolith for the MVP."
  },
  "date": "2026-10-24"
}
```

Until `human_decision.decided_by` identifies the human sponsor (or another explicitly authorized human) and `human_decision.decision` is non-empty, the record is unresolved. The detector matches `decided_by` exactly: a username listed in `.claude/human-approvers.json` when that file exists, otherwise only `human sponsor`, `sponsor` or `human`. Writing a disagreement record prompts the human (`ask` rule in `.claude/settings.json`). Do not invent a decision, date, or approver. Record the actual decision and date after the human responds.

## Mandatory stop rule

No agent may ignore, bypass, silently close, or work around an escalated disagreement. Before **every orchestration transition**, run:

```bash
python scripts/detect_conflict.py --story <story> --agents <agent-a,agent-b>
```

Exit code:

- `0`: no matching story conflict exists, or all matching records contain a valid human decision.
- `1`: at least one matching conflict exists without a valid human decision; **STOP** the transition and escalate to the human.
- `2`: invalid invocation, unreadable record, or malformed JSON; fail closed and **STOP** the transition.

The detector is read-only. The orchestrator records the blocker and requested decision, and resumes only after the record is valid and the human decision is present.
