"""Tests for the deterministic model-tier router and its drift guard against the routing document."""

import re
import unittest
from pathlib import Path

from scripts import route_model

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "model-routing-decision.md").read_text(encoding="utf-8")


def route(agent, skill, size="M", risk=False, retry=False, no_production_code=False):
    return route_model.route(agent, skill, size, risk, retry, no_production_code)


class RouteModelTests(unittest.TestCase):
    def test_worked_examples_from_the_routing_document(self):
        readme = route("documentation-manager", "documentation-session-handover", "XS", no_production_code=True)
        self.assertEqual((readme["tier"], readme["set_model_on_delegation"]), ("light", "haiku"))
        auth = route("backend-developer", "backend-engineering-standards", "M", risk=True)
        self.assertEqual((auth["tier"], auth["set_model_on_delegation"]), ("premium", "opus"))
        first = route("qa-automation", "debugging-root-cause-analysis")
        self.assertEqual((first["tier"], first["set_model_on_delegation"]), ("standard", None))
        retry = route("qa-automation", "debugging-root-cause-analysis", retry=True)
        self.assertEqual(retry["tier"], "premium")
        review = route("code-review-security", "code-review-refactoring", "XS", no_production_code=True)
        self.assertEqual((review["tier"], review["set_model_on_delegation"]), ("premium", None))

    def test_bounds_and_single_raise(self):
        self.assertEqual(route("ci-verifier", "security-threat-modelling", "L", risk=True)["tier"], "light")
        self.assertEqual(route("backend-developer", "git-github-workflows", "XS")["tier"], "standard")
        # Several raise reasons still raise once, and never past premium.
        self.assertEqual(route("product-owner", "agile-planning", "L", risk=True, retry=True)["tier"], "premium")
        self.assertEqual(route("software-architect", "architecture-evaluation-adr", "L")["tier"], "premium")
        # A raise blocks the XS lowering.
        self.assertEqual(route("product-owner", "agile-planning", "XS", risk=True, no_production_code=True)["tier"], "premium")

    def test_invalid_inputs_exit_two(self):
        for argv in (
            ["--agent", "backend-developer", "--skill", "backend-engineering-standards", "--size", "XL"],
            ["--agent", "backend-developer", "--skill", "no-such-skill", "--size", "M"],
            ["--agent", "no-such-agent", "--skill", "agile-planning", "--size", "M"],
            ["--agent", "agile-orchestrator", "--skill", "agile-planning", "--size", "M"],
        ):
            with self.subTest(argv=argv):
                self.assertEqual(route_model.main(argv), 2)

    def test_every_skill_has_a_tier(self):
        skills = {path.parent.name for path in (ROOT / ".claude" / "skills").glob("*/SKILL.md")}
        self.assertEqual(skills, set(route_model.SKILL_TIERS))

    def test_skill_tiers_match_the_routing_document(self):
        table = DOC.split("### Complexity tier per skill", 1)[1].split("###", 1)[0]
        documented = dict(re.findall(r"(?m)^\| `([a-z0-9-]+)` \| (light|standard|premium) \|", table))
        self.assertEqual(documented, route_model.SKILL_TIERS)

    def test_agent_bounds_match_the_routing_document(self):
        table = DOC.split("**Clamp to the agent's bounds:**", 1)[1].split("5. **Apply", 1)[0]
        bounds = {
            "premium only": ("premium", "premium"),
            "light only": ("light", "light"),
            "standard–premium": ("standard", "premium"),
        }
        documented = {}
        for agents, rule in re.findall(r"(?m)^\s*\| ((?:`[a-z0-9-]+`(?:, )?)+) \| ([^|.]+)", table):
            key = next(name for name in bounds if rule.strip().startswith(name))
            documented.update({agent: bounds[key] for agent in re.findall(r"`([a-z0-9-]+)`", agents)})
        self.assertEqual(documented, route_model.AGENT_BOUNDS)
        self.assertIn("| All other specialists | light–premium |", table)


if __name__ == "__main__":
    unittest.main()
