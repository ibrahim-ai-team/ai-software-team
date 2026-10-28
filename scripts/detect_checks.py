"""List which of ci-verifier's allowlisted checks apply to a repository, from the files present (read-only).

Prints JSON: `applicable` (command, G2 evidence key, reason) and `not_applicable` (command, reason).
It never runs a check and never infers a result; ci-verifier runs the listed commands and reports
what it observes. The secret scan is always applicable because G2 requires it.
"""

from __future__ import annotations

import argparse
import configparser
import json
import re
import sys
from pathlib import Path

PLACEHOLDER_NPM_TEST = "no test specified"


def _pyproject_has(repo: Path, tool: str) -> bool:
    """Whether pyproject.toml has a [tool.<tool>...] table (a section match, identical on every Python version)."""
    path = repo / "pyproject.toml"
    try:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeError):
        return False
    return re.search(rf"(?m)^\[tool\.{re.escape(tool)}[\].]", text) is not None


def _uses_pytest(repo: Path) -> bool:
    if (repo / "pytest.ini").is_file() or (repo / "conftest.py").is_file() or (repo / "tests" / "conftest.py").is_file():
        return True
    if _pyproject_has(repo, "pytest"):
        return True
    setup_cfg = repo / "setup.cfg"
    if setup_cfg.is_file():
        parser = configparser.ConfigParser()
        try:
            parser.read(setup_cfg, encoding="utf-8")
        except configparser.Error:
            return False
        return parser.has_section("tool:pytest")
    return False


def _make_targets(repo: Path) -> set[str]:
    path = repo / "Makefile"
    if not path.is_file():
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return set()
    return set(re.findall(r"(?m)^([A-Za-z0-9_.-]+)\s*:(?!=)", text))


def _npm_scripts(repo: Path) -> dict[str, str] | None:
    path = repo / "package.json"
    if not path.is_file():
        return None
    try:
        scripts = json.loads(path.read_text(encoding="utf-8")).get("scripts", {})
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
        return {}
    return {k: v for k, v in scripts.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(scripts, dict) else {}


def detect(repo: Path) -> dict:
    applicable: list[dict] = []
    not_applicable: list[dict] = []

    def add(command: str, evidence: str, reason: str) -> None:
        applicable.append({"command": command, "evidence": evidence, "reason": reason})

    def skip(command: str, reason: str) -> None:
        not_applicable.append({"command": command, "reason": reason})

    python_tests = any((repo / "tests").glob("test_*.py")) if (repo / "tests").is_dir() else False
    if _uses_pytest(repo):
        add("python -m pytest -q", "tests", "pytest configuration found")
    elif python_tests:
        add("python -m unittest discover -s tests", "tests", "tests/test_*.py found without pytest configuration")
    else:
        skip("python -m unittest discover -s tests", "no Python tests found")

    if (repo / "ruff.toml").is_file() or (repo / ".ruff.toml").is_file() or _pyproject_has(repo, "ruff"):
        add("ruff check", "lint", "Ruff configuration found")
        add("ruff format --check", "lint", "Ruff configuration found")
    else:
        skip("ruff check", "no Ruff configuration")

    npm = _npm_scripts(repo)
    for script, command, evidence in (
        ("test", "npm test", "tests"),
        ("lint", "npm run lint", "lint"),
        ("build", "npm run build", "build"),
    ):
        if npm is None:
            skip(command, "no package.json")
        elif script not in npm or (script == "test" and PLACEHOLDER_NPM_TEST in npm[script]):
            skip(command, f"package.json has no real '{script}' script")
        else:
            add(command, evidence, f"package.json defines '{script}'")

    targets = _make_targets(repo)
    for target, evidence in (("test", "tests"), ("lint", "lint")):
        if target in targets:
            add(f"make {target}", evidence, f"Makefile defines '{target}'")
        else:
            skip(f"make {target}", f"no Makefile target '{target}'")

    add("gitleaks detect --no-git", "secrets", "secret scanning is mandatory for G2")
    missing = sorted({"lint", "tests", "secrets"} - {check["evidence"] for check in applicable})
    return {"applicable": applicable, "not_applicable": not_applicable, "g2_evidence_without_a_check": missing}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository or worktree to inspect (default: current directory)")
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    if not repo.is_dir():
        print(f"ERROR: not a directory: {repo}", file=sys.stderr)
        return 2
    print(json.dumps(detect(repo), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
