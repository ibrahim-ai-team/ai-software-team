"""Regression tests for the public static validator contract."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".claude" / "agents"


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fields = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


class ValidatorRegressionTests(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/validate_team.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_validator_rejects_missing_license_standard(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            (copy / "standards/license-risk.md").unlink()
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Missing required", result.stdout)

    def test_static_validator_passes(self):
        result = self.run_validator(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_every_agent_has_an_explicit_tools_allowlist(self):
        agents = sorted(AGENTS.glob("*.md"))
        self.assertTrue(agents, "No agent definitions found")
        for path in agents:
            with self.subTest(agent=path.name):
                tools = read_frontmatter(path).get("tools", "").strip()
                self.assertTrue(tools, f"{path.relative_to(ROOT)} has no tools allowlist")
                self.assertEqual(
                    len([tool.strip() for tool in tools.split(",") if tool.strip()]),
                    len(set(tool.strip() for tool in tools.split(",") if tool.strip())),
                    f"{path.relative_to(ROOT)} has duplicate tools",
                )

    def test_security_reviewer_is_read_only(self):
        path = AGENTS / "code-review-security.md"
        self.assertTrue(path.is_file(), "Security reviewer agent is missing")
        tools = {tool.strip() for tool in read_frontmatter(path).get("tools", "").split(",") if tool.strip()}
        forbidden = {"Edit", "Write", "Bash"} & tools
        self.assertFalse(forbidden, f"Security reviewer must remain read-only: {sorted(forbidden)}")

    def test_validator_rejects_empty_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            (copy / ".claude/commands/status.md").write_text("", encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Empty required command", result.stdout)

    def test_validator_rejects_missing_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            (copy / ".claude/commands/kickoff.md").unlink()
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Missing required command", result.stdout)

    def test_validator_rejects_removed_permission_guardrail(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            settings = copy / ".claude/settings.json"
            settings.write_text('{"permissions":{"deny":[]}}\n', encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("permission deny rule missing", result.stdout)

    def test_mock_discovery_smoke_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/smoke_discovery.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OFFLINE INVENTORY CHECK PASS", result.stdout)

    def test_manifest_drives_inventory_minimums(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            manifest_path = copy / ".claude/manifest.json"
            import json

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["inventory"]["agents"]["minimum_count"] = 999
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("manifest requires at least 999 agents", result.stdout.lower())

    def test_validator_rejects_invalid_manifest_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            (copy / ".claude/manifest.json").write_text('{"schema_version":99,"inventory":{}}', encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Unsupported or missing manifest schema_version", result.stdout)

    def test_validator_rejects_writable_validation_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            workflow = copy / ".github/workflows/validate-team.yml"
            text = workflow.read_text(encoding="utf-8").replace("contents: read", "contents: write")
            workflow.write_text(text, encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("read-only", result.stdout)

    def test_validator_rejects_manifest_minimum_below_hard_floor(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            import json

            path = copy / ".claude/manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["inventory"]["agents"]["minimum_count"] = 17
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("hard floor 18", result.stdout)

    def test_validator_rejects_manifest_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            import json

            path = copy / ".claude/manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["inventory"]["agents"]["directory"] = "../outside"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("must stay inside the repository", result.stdout)

    def test_validator_rejects_missing_command_description(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            path = copy / ".claude/commands/status.md"
            path.write_text(path.read_text(encoding="utf-8").replace("description:", "summary:", 1), encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Missing or empty 'description'", result.stdout)

    def test_validator_rejects_secret_workflow_write_permission(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            path = copy / ".github/workflows/secret-scan.yml"
            path.write_text(path.read_text(encoding="utf-8").replace("contents: read", "contents: write"), encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("read-only", result.stdout)

    def test_validator_rejects_unpinned_checkout_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            path = copy / ".github/workflows/validate-team.yml"
            text = path.read_text(encoding="utf-8").replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", "actions/checkout@v7"
            )
            path.write_text(text, encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("full commit SHAs", result.stdout)

    def test_validator_rejects_agent_reference_to_missing_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            path = copy / ".claude/agents/backend-developer.md"
            text = path.read_text(encoding="utf-8").replace(
                ".claude/skills/backend-engineering-standards/SKILL.md",
                ".claude/skills/does-not-exist/SKILL.md",
            )
            path.write_text(text, encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("references a missing skill", result.stdout)

    def test_validator_rejects_agent_without_skill_routing_section(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            path = copy / ".claude/agents/documentation-manager.md"
            text = path.read_text(encoding="utf-8")
            start = text.index("## Relevant skills")
            end = text.index("## Evidence contract", start)
            path.write_text(text[:start] + text[end:], encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("missing a Relevant skills section", result.stdout)

    def test_validator_rejects_missing_high_risk_command_deny(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            settings_path = copy / ".claude/settings.json"
            import json

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            settings["permissions"]["deny"].remove("Bash(terraform apply*)")
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Bash(terraform apply*)", result.stdout)

    def test_validator_rejects_missing_secret_read_deny(self):
        for rule in ("Read(./.env.*)", "Read(./**/*.pem)", "Read(./**/*.key)"):
            with self.subTest(rule=rule), tempfile.TemporaryDirectory() as temporary:
                copy = Path(temporary) / "repo"
                shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
                settings_path = copy / ".claude/settings.json"
                import json

                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                settings["permissions"]["deny"].remove(rule)
                settings_path.write_text(json.dumps(settings), encoding="utf-8")
                result = self.run_validator(copy)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(rule, result.stdout)

    def test_validator_reports_non_object_manifest_without_crashing(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
            (copy / ".claude/manifest.json").write_text("[]", encoding="utf-8")
            result = self.run_validator(copy)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Manifest root must be a JSON object", result.stdout)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
