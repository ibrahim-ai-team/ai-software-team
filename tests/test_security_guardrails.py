"""Security guardrail tests for .claude/settings.json.

IMPORTANT: these are simulated rule-matching tests and validator regression tests.
They never execute the commands being tested and do not prove Claude Code runtime
enforcement. See docs/security-guardrails.md for the runtime procedure.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"


def load_rules():
    permissions = json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"]
    return permissions.get("deny", []), permissions.get("ask", []), permissions.get("allow", [])


def parse_rule(rule):
    match = re.fullmatch(r"(\w+)\((.*)\)", rule, re.S)
    return (match.group(1), match.group(2)) if match else (rule, None)


def bash_match(pattern, command):
    regex = ".*".join(re.escape(part) for part in pattern.split("*"))
    return re.fullmatch(regex, command.strip(), re.S) is not None


def path_match(pattern, path):
    if not path.startswith("./"):
        path = "./" + path
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.fullmatch(out, path) is not None


def decide(tool, argument):
    deny, ask, _allow = load_rules()
    for label, rules in (("deny", deny), ("ask", ask)):
        for rule in rules:
            rule_tool, spec = parse_rule(rule)
            if rule_tool != tool or spec is None:
                continue
            hit = bash_match(spec, argument) if tool == "Bash" else path_match(spec, argument)
            if hit:
                return label
    return "allow"


class SimulatedRuleMatching(unittest.TestCase):
    """SIMULATED matcher semantics; not Claude Code runtime behavior."""

    def assert_decisions(self, tool, expected, items):
        for argument in items:
            with self.subTest(tool=tool, argument=argument):
                self.assertEqual(decide(tool, argument), expected)

    def test_dangerous_bash_commands_are_denied(self):
        self.assert_decisions("Bash", "deny", [
            "git push origin HEAD:main", "git push origin HEAD:refs/heads/main",
            "git push --force", "git push --force-with-lease",
            "git push origin feat/x --force", "git push origin feat/x --force-with-lease",
            "git push -f origin feat/x", "git push origin feat/x -f", "git push origin +feat/x",
            "git push upstream main", "git push origin :main", "git push origin --delete feat/x",
            "git push --mirror", "git reset --hard HEAD~1", "git clean -fd",
            "rm -rf build", "rm -fr build", "rm -Rf build", "rm --recursive --force build",
            "gh pr merge 5", "gh repo delete owner/repo", "gh auth token",
            "gh auth status --show-token", "terraform apply", "kubectl delete pod x",
        ])

    def test_secret_reads_through_common_tools_are_denied(self):
        self.assert_decisions("Bash", "deny", [
            "cat .env", "cat config/.env.local", "head -5 .env", "tail -n 3 .env",
            "grep API_KEY .env", "sed -n 1,5p .env", "awk '{print}' .env",
            "source .env", "printenv", "printenv HOME",
        ])

    def test_file_tool_secret_and_edit_rules(self):
        self.assert_decisions("Read", "deny", ["./.env", "./.env.local", "./keys/a.pem", "./x/y/id.key", "./secrets/token.txt"])
        self.assert_decisions("Edit", "deny", ["./.env", "./.env.prod", "./certs/server.pem", "./secrets/a.txt"])

    def test_sensitive_configuration_requires_confirmation(self):
        protected_paths = [
            "./.claude/settings.json", "./.github/workflows/validate-team.yml",
            "./.github/workflows/secret-scan.yml", "./.github/CODEOWNERS",
            "./.github/dependabot.yml", "./.claude/CLAUDE.md",
            "./.claude/manifest.json",
        ]
        self.assert_decisions("Edit", "ask", protected_paths)
        self.assert_decisions("Write", "ask", protected_paths)

    def test_other_pushes_and_risky_operations_ask(self):
        self.assert_decisions("Bash", "ask", [
            "git push origin feat/security-guardrails-sprint-1", "git push", "git push origin feat/domain",
            "git push origin feature/main-fix", "rm -r build", "rm -R build",
            "gh api repos/o/r/branches/main/protection", "gh repo edit --visibility public", "gh secret set X",
        ])

    def test_ordinary_development_commands_are_not_blocked(self):
        self.assert_decisions("Bash", "allow", [
            "git status", "git diff --stat", "git log --oneline -5", "git checkout -b feat/x",
            "git commit -m 'update docs'", "git fetch origin main", "python3 scripts/validate_team.py",
            "python3 -m unittest discover -s tests", "grep -rn TODO docs", "head -20 README.md",
            "sed -n 1,5p CHANGELOG.md", "rm temp.txt", "ls -la",
        ])
        self.assert_decisions("Read", "allow", ["./README.md", "./docs/security-guardrails.md"])
        self.assert_decisions("Edit", "allow", ["./README.md", "./docs/security-guardrails.md", "./tests/test_security_guardrails.py"])

    def test_documented_bypasses_are_not_matched_by_rules(self):
        self.assert_decisions("Bash", "allow", [
            "python3 -c \"print(open('.env').read())\"",
            "bash -c 'git push --force'",
            "env GIT_TERMINAL_PROMPT=0 git push --force",
            "perl -pe '' .env",
        ])
        doc = (ROOT / "docs" / "security-guardrails.md").read_text(encoding="utf-8")
        for phrase in ("python", "bash -c", "sandbox"):
            self.assertIn(phrase.casefold(), doc.casefold(), f"limitation not documented: {phrase}")


class ValidatorRejectsWeakenedGuardrails(unittest.TestCase):
    """Proves the static gate fails, not runtime enforcement."""

    def run_mutated(self, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repo"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            settings_path = target / ".claude" / "settings.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            mutate(settings["permissions"])
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            return subprocess.run([sys.executable, "scripts/validate_team.py"], cwd=target,
                                  capture_output=True, text=True, check=False)

    def assert_rejected(self, mutate, message):
        result = self.run_mutated(mutate)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(message, result.stdout)

    def test_unmodified_repository_passes(self):
        self.assertEqual(self.run_mutated(lambda permissions: None).returncode, 0)

    def test_rejects_missing_force_push_flag_variant(self):
        self.assert_rejected(lambda p: p["deny"].remove("Bash(git push*--force*)"), "deny rule missing: Bash(git push*--force*)")

    def test_rejects_missing_protected_branch_refspec_rule(self):
        self.assert_rejected(lambda p: p["deny"].remove("Bash(git push*:refs/heads/main*)"), "deny rule missing")

    def test_rejects_missing_recursive_delete_variant(self):
        self.assert_rejected(lambda p: p["deny"].remove("Bash(rm -fr*)"), "deny rule missing: Bash(rm -fr*)")

    def test_rejects_missing_env_edit_protection(self):
        self.assert_rejected(lambda p: p["deny"].remove("Edit(./.env)"), "deny rule missing: Edit(./.env)")

    def test_rejects_missing_mcp_merge_tool_denial(self):
        self.assert_rejected(lambda p: p["deny"].remove("mcp__github__merge_pull_request"),
                             "deny rule missing: mcp__github__merge_pull_request")

    def test_rejects_missing_credential_exposure_rule(self):
        self.assert_rejected(lambda p: p["deny"].remove("Bash(gh auth token*)"), "deny rule missing: Bash(gh auth token*)")

    def test_rejects_missing_settings_confirmation_rule(self):
        self.assert_rejected(lambda p: p["ask"].remove("Edit(./.claude/settings.json)"), "ask rule missing")

    def test_rejects_missing_workflow_confirmation_rule(self):
        self.assert_rejected(lambda p: p["ask"].remove("Edit(./.github/workflows/**)"), "ask rule missing")

    def test_rejects_removed_ask_section(self):
        self.assert_rejected(lambda p: p.pop("ask"), "ask rule missing")

    def test_rejects_unrestricted_allow_rule(self):
        self.assert_rejected(lambda p: p.__setitem__("allow", ["Bash(*)"]), "allow rule is unrestricted")

    def test_rejects_rule_that_is_allowed_and_denied(self):
        self.assert_rejected(lambda p: p.__setitem__("allow", ["Bash(rm -fr*)"]), "both allowed and denied")

    def test_rejects_non_list_rules(self):
        self.assert_rejected(lambda p: p.__setitem__("ask", "Bash(git push*)"), "must be a list of strings")

    def test_rejects_duplicate_rules(self):
        self.assert_rejected(lambda p: p["ask"].append("Bash(git push*)"), "contain duplicates")


if __name__ == "__main__":
    unittest.main()
