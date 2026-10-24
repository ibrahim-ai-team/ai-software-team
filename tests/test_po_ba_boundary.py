"""Regression tests for the Product Owner / Business Analyst boundary."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PoBaBoundaryTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_business_analyst_is_spec_owner(self) -> None:
        content = self.read(".claude/agents/business-analyst.md")
        self.assertIn("You are the OWNER of the EARS specification", content)
        self.assertIn("You do NOT decide priority or scope", content)

    def test_product_owner_validates_but_does_not_write_spec(self) -> None:
        content = self.read(".claude/agents/product-owner.md")
        self.assertIn("You do NOT write the EARS specification", content)
        self.assertIn("You VALIDATE the specification produced by the BA", content)
        self.assertIn("Never rewrite the specification yourself", content)

    def test_contract_names_boundary_and_both_role_limits(self) -> None:
        content = self.read("standards/agent-contract.md")
        self.assertIn("Product Owner vs Business Analyst: responsibility boundary", content)
        self.assertIn("The PO does not write the formal EARS specification", content)
        self.assertIn("The BA does not decide business priority or scope", content)
        self.assertIn("A human approves at **CP1**", content)

    def test_bootstrap_order_is_explicit(self) -> None:
        content = self.read("workflows/project-bootstrap.md")
        self.assertIn("Product Owner — business-value brief", content)
        self.assertIn("Business Analyst — EARS specification", content)
        self.assertIn("Product Owner — business validation", content)
        self.assertIn("Human — CP1", content)

    def test_template_separates_business_value_and_specification(self) -> None:
        content = self.read("templates/spec-ears.md")
        self.assertIn("Author: business-analyst. Validator: product-owner. Human approver: CP1.", content)
        self.assertIn("## Business value (PO)", content)
        self.assertIn("## Specification (BA)", content)

    def test_ambiguous_en_collaboration_wording_is_rejected(self) -> None:
        for path in (".claude/agents/business-analyst.md", ".claude/agents/product-owner.md"):
            content = self.read(path)
            for line in content.splitlines():
                if re.search(r"\bin collaboration\b", line, re.IGNORECASE):
                    self.assertRegex(
                        line,
                        r"(BA|business-analyst|Business Analyst).*(write|author|produce|specification)",
                        msg=f"Ambiguous collaboration wording in {path}: {line}",
                    )


if __name__ == "__main__":
    unittest.main()
