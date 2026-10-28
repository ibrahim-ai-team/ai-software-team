"""Tests for the deterministic applicable-check detector used by ci-verifier."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts import detect_checks

ROOT = Path(__file__).resolve().parents[1]


def commands(result, key="applicable"):
    return [check["command"] for check in result[key]]


class DetectChecksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)

    def write(self, relative, text):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_this_repository(self):
        result = detect_checks.detect(ROOT)
        self.assertEqual(
            commands(result),
            ["python -m unittest discover -s tests", "ruff check", "ruff format --check", "gitleaks detect --no-git"],
        )
        self.assertEqual(result["g2_evidence_without_a_check"], [])

    def test_empty_repository_still_requires_the_secret_scan(self):
        result = detect_checks.detect(self.repo)
        self.assertEqual(commands(result), ["gitleaks detect --no-git"])
        self.assertEqual(result["g2_evidence_without_a_check"], ["lint", "tests"])

    def test_pytest_configuration_in_pyproject(self):
        self.write("pyproject.toml", "[tool.pytest.ini_options]\naddopts = '-q'\n\n[tool.ruff.lint]\nselect = ['E']\n")
        self.write("tests/test_x.py", "")
        found = commands(detect_checks.detect(self.repo))
        self.assertIn("python -m pytest -q", found)
        self.assertNotIn("python -m unittest discover -s tests", found)
        self.assertIn("ruff check", found)

    def test_npm_scripts_and_placeholder_test(self):
        scripts = {"test": 'echo "Error: no test specified" && exit 1', "lint": "eslint .", "build": "vite build"}
        self.write("package.json", json.dumps({"scripts": scripts}))
        result = detect_checks.detect(self.repo)
        self.assertEqual(commands(result), ["npm run lint", "npm run build", "gitleaks detect --no-git"])
        self.assertIn("npm test", commands(result, "not_applicable"))

    def test_makefile_targets(self):
        self.write("Makefile", ".PHONY: test\nVAR := 1\ntest:\n\tpytest\n")
        found = commands(detect_checks.detect(self.repo))
        self.assertIn("make test", found)
        self.assertNotIn("make lint", found)

    def test_malformed_package_json_is_not_applicable(self):
        self.write("package.json", "{")
        self.assertNotIn("npm test", commands(detect_checks.detect(self.repo)))

    def test_ci_verifier_allowlist_includes_the_detector(self):
        # ci-verifier refuses unlisted commands, so the detector it is told to run must be in its closed allowlist.
        text = (ROOT / ".claude" / "agents" / "ci-verifier.md").read_text(encoding="utf-8")
        allowlist = text.split("## Closed command allowlist", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`python scripts/detect_checks.py`", allowlist)

    def test_missing_directory_exits_two(self):
        self.assertEqual(detect_checks.main(["--repo", str(self.repo / "nope")]), 2)


if __name__ == "__main__":
    unittest.main()
