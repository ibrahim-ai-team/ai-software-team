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
        self.assertIn("Tu es le PROPRIÉTAIRE de la spec EARS", content)
        self.assertIn("Tu ne décides PAS de la priorité ni du scope", content)

    def test_product_owner_validates_but_does_not_write_spec(self) -> None:
        content = self.read(".claude/agents/product-owner.md")
        self.assertIn("Tu ne rédiges PAS la spec EARS", content)
        self.assertIn("Tu VALIDES la spec produite par le BA", content)
        self.assertIn("Tu ne réécris jamais la spec toi-même", content)

    def test_contract_names_boundary_and_both_role_limits(self) -> None:
        content = self.read("standards/agent-contract.md")
        self.assertIn("PO vs BA : séparation des responsabilités", content)
        self.assertIn("Le PO ne rédige pas la spécification EARS", content)
        self.assertIn("Le BA ne décide ni de la priorité ni du scope métier", content)
        self.assertIn("L'humain approuve à **CP1**", content)

    def test_bootstrap_order_is_explicit(self) -> None:
        content = self.read("workflows/project-bootstrap.md")
        self.assertIn("Product Owner — brief de valeur métier", content)
        self.assertIn("Business Analyst — spec EARS", content)
        self.assertIn("Product Owner — validation métier", content)
        self.assertIn("Humain — CP1", content)

    def test_template_separates_business_value_and_specification(self) -> None:
        content = self.read("templates/spec-ears.md")
        self.assertIn("Auteur : business-analyst. Validateur : product-owner. Approbateur humain : CP1.", content)
        self.assertIn("## Valeur métier (PO)", content)
        self.assertIn("## Spécification (BA)", content)

    def test_ambiguous_en_collaboration_wording_is_rejected(self) -> None:
        for path in (".claude/agents/business-analyst.md", ".claude/agents/product-owner.md"):
            content = self.read(path)
            for line in content.splitlines():
                if re.search(r"\ben collaboration\b", line, re.IGNORECASE):
                    self.assertRegex(
                        line,
                        r"(BA|business-analyst|Business Analyst).*(écrit|rédig|auteur|produit la spec)",
                        msg=f"Ambiguous collaboration wording in {path}: {line}",
                    )


if __name__ == "__main__":
    unittest.main()
