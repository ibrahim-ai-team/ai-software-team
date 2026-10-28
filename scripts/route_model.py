"""Compute a delegation's model tier with the rules in docs/model-routing-decision.md (read-only).

The orchestrator supplies the judgment inputs (primary skill, size, whether the change is
security-sensitive, whether the previous attempt failed); this script applies the fixed algorithm:
base tier from the skill, raise or lower, clamp to the agent's bounds, compare with the agent's default.
Prints JSON. Exit 0 on success, 2 on invalid input (including XL, which must be split).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".claude" / "agents"
TIERS = ("light", "standard", "premium")
ALIASES = {"light": "haiku", "standard": "sonnet", "premium": "opus"}
# Mirrors the tables in docs/model-routing-decision.md; tests/test_route_model.py fails if they drift.
SKILL_TIERS = {
    "git-github-workflows": "light",
    "token-context-cost-management": "light",
    "documentation-session-handover": "light",
    "agile-planning": "standard",
    "requirements-analysis": "standard",
    "user-stories-acceptance-criteria": "standard",
    "ui-ux-design-system": "standard",
    "accessibility-review": "standard",
    "frontend-engineering-standards": "standard",
    "backend-engineering-standards": "standard",
    "api-design-documentation": "standard",
    "database-modelling-migrations": "standard",
    "test-strategy-automation": "standard",
    "debugging-root-cause-analysis": "standard",
    "code-review-refactoring": "standard",
    "docker-cicd": "standard",
    "observability-sre": "standard",
    "performance-testing": "standard",
    "release-management": "standard",
    "technical-research-source-verification": "standard",
    "architecture-evaluation-adr": "premium",
    "technology-stack-selection": "premium",
    "security-threat-modelling": "premium",
}
_CODE_AGENTS = ("backend-developer", "frontend-developer", "database-engineer", "devops-platform", "qa-automation")
AGENT_BOUNDS = {
    "software-architect": ("premium", "premium"),
    "code-review-security": ("premium", "premium"),
    "ci-verifier": ("light", "light"),
    "github-integration": ("light", "light"),
    **{agent: ("standard", "premium") for agent in (*_CODE_AGENTS, "performance-engineer", "tech-lead")},
}
DEFAULT_BOUNDS = ("light", "premium")


def default_alias(agent: str) -> str | None:
    """The agent's frontmatter `model` alias, or None when the file or field is missing."""
    path = AGENTS_DIR / f"{agent}.md"
    if not path.is_file():
        return None
    frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
    match = re.search(r"(?m)^model:\s*(\S+)\s*$", frontmatter)
    return match.group(1) if match else None


def route(agent: str, skill: str, size: str, risk: bool, retry: bool, no_production_code: bool) -> dict:
    if size == "XL":
        raise ValueError("size XL must be split before it is delegated (standards/sprint-sizing.md)")
    if skill not in SKILL_TIERS:
        raise ValueError(f"unknown skill: {skill}")
    alias = default_alias(agent)
    if alias is None:
        raise ValueError(f"unknown agent or agent without a model default: {agent}")
    reasons = [f"base {SKILL_TIERS[skill]} from skill {skill}"]
    level = TIERS.index(SKILL_TIERS[skill])
    raise_because = [
        name
        for name, applies in (
            ("size L", size == "L"),
            ("security-sensitive change", risk),
            ("retry after a failed attempt", retry),
        )
        if applies
    ]
    if raise_because:
        if level < len(TIERS) - 1:
            level += 1
            reasons.append(f"raised one tier: {', '.join(raise_because)}")
    elif size == "XS" and TIERS[level] == "standard" and no_production_code:
        level -= 1
        reasons.append("lowered one tier: XS with no production code or tests")
    low, high = AGENT_BOUNDS.get(agent, DEFAULT_BOUNDS)
    clamped = min(max(level, TIERS.index(low)), TIERS.index(high))
    if clamped != level:
        reasons.append(f"clamped to {agent}'s allowed tiers {low}–{high}")
    tier = TIERS[clamped]
    override = ALIASES[tier] != alias
    return {
        "agent": agent,
        "skill": skill,
        "tier": tier,
        "alias": ALIASES[tier],
        "agent_default": alias,
        "set_model_on_delegation": ALIASES[tier] if override else None,
        "reasons": reasons,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--skill", required=True, help="the task's primary skill, as named first in the brief")
    parser.add_argument("--size", required=True, choices=("XS", "S", "M", "L", "XL"))
    parser.add_argument("--risk", action="store_true", help="touches auth, payments, personal data, secrets or existing data")
    parser.add_argument("--retry", action="store_true", help="the previous attempt failed or hit its turn cap")
    parser.add_argument(
        "--no-production-code", action="store_true", help="docs, config copy, board updates or report formatting only"
    )
    args = parser.parse_args(argv)
    if args.agent == "agile-orchestrator":
        print("ERROR: the orchestrator is not routed; it keeps the session model", file=sys.stderr)
        return 2
    try:
        result = route(args.agent, args.skill, args.size, args.risk, args.retry, args.no_production_code)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
