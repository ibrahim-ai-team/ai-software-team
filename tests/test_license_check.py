"""Regression tests for the standard-library dependency license checker."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_licenses


class LicenseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_empty_dependency_inputs_pass_and_list_none(self):
        rows, errors = check_licenses.check(self.root)
        self.assertEqual(rows, [])
        self.assertEqual(errors, [])

    def test_requirements_and_pyproject_dependencies_are_collected(self):
        (self.root / "requirements.txt").write_text("requests>=2.0\n# comment\nfoo-bar==1.0\n", encoding="utf-8")
        (self.root / "pyproject.toml").write_text(
            '[project]\ndependencies = ["requests>=2.0", "Example_Pkg~=1.0"]\n'
            '[project.optional-dependencies]\ntest = ["pytest>=7"]\n',
            encoding="utf-8",
        )
        self.assertEqual(
            check_licenses.declared_dependencies(self.root),
            ["Example_Pkg", "foo-bar", "pytest", "requests"],
        )

    def test_gpl3_and_agpl_are_prohibited(self):
        with patch.object(check_licenses, "distribution_license", side_effect=["GPL-3.0-only", "AGPL-3.0-or-later"]):
            (self.root / "requirements.txt").write_text("package-one\npackage-two\n", encoding="utf-8")
            rows, errors = check_licenses.check(self.root)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("GPL-3.0" in error for error in errors))
        self.assertTrue(any("AGPL" in error for error in errors))

    def test_unknown_license_fails_closed(self):
        with patch.object(check_licenses, "distribution_license", return_value="UNKNOWN"):
            (self.root / "requirements.txt").write_text("unknown-package\n", encoding="utf-8")
            _rows, errors = check_licenses.check(self.root)
        self.assertTrue(any("metadata is missing" in error for error in errors))

    def test_missing_distribution_metadata_fails_closed(self):
        with patch.object(
            check_licenses,
            "distribution_license",
            side_effect=ValueError("license metadata not found for declared dependency 'missing'; install it to verify"),
        ):
            (self.root / "requirements.txt").write_text("missing\n", encoding="utf-8")
            rows, errors = check_licenses.check(self.root)
        self.assertEqual(rows, [("missing", "UNVERIFIED")])
        self.assertTrue(errors)

    def test_license_allowlist_examples_are_not_prohibited(self):
        for license_name in ("MIT", "Apache-2.0", "BSD-3-Clause", "ISC", "Python Software Foundation License"):
            with self.subTest(license_name=license_name):
                self.assertIsNone(check_licenses.FORBIDDEN.search(license_name))


if __name__ == "__main__":
    unittest.main()
