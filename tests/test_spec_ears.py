"""Regression tests for EARS-formatted story specifications."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_TEMPLATE = ROOT / "templates" / "spec-ears.md"
EARS_PREFIXES = ("When ", "If ", "While ")


def has_ears_requirement(spec_text: str) -> bool:
    """Return whether the spec contains at least one EARS requirement line."""
    for line in spec_text.splitlines():
        statement = line.strip()
        if statement.startswith(EARS_PREFIXES) and "shall" in statement:
            return True
    return False


class SpecEarsTests(unittest.TestCase):
    def test_template_contains_ears_requirement(self):
        self.assertTrue(has_ears_requirement(SPEC_TEMPLATE.read_text(encoding="utf-8")))

    def test_when_statement_with_shall_is_accepted(self):
        self.assertTrue(has_ears_requirement("When a user saves, the system shall persist the record."))

    def test_if_statement_with_shall_is_accepted(self):
        self.assertTrue(has_ears_requirement("If input is invalid, then the system shall show an error."))

    def test_while_statement_with_shall_is_accepted(self):
        self.assertTrue(has_ears_requirement("While offline, the system shall queue the update."))

    def test_spec_without_ears_requirement_is_rejected(self):
        self.assertFalse(has_ears_requirement("The system should do X."))

    def test_empty_spec_is_rejected(self):
        self.assertFalse(has_ears_requirement(""))

    def test_trigger_without_shall_is_rejected(self):
        self.assertFalse(has_ears_requirement("When a user saves, the system stores the record."))


if __name__ == "__main__":
    unittest.main()
