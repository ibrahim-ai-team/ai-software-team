#!/usr/bin/env python3
"""Check declared Python dependencies using only the Python standard library."""

import argparse
import importlib.metadata
import re
import sys
from pathlib import Path

PACKAGE_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
FORBIDDEN = re.compile(
    r"\b(?:AGPL(?:-[0-9.]+(?:-(?:only|or-later))?)?|"
    r"GNU Affero General Public License|GPLv3|GNU General Public License v3|"
    r"GPL-3(?:\.0)?(?:\+(?:only|or-later)?|-(?:only|or-later))?)\b",
    re.IGNORECASE,
)


def parse_requirements(path: Path) -> set[str]:
    names: set[str] = set()
    if not path.is_file():
        return names
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http:", "https:")):
            continue
        match = PACKAGE_NAME.match(line)
        if match:
            names.add(match.group(1))
    return names


def parse_pyproject(path: Path) -> set[str]:
    """Extract PEP 621 dependencies without adding a TOML dependency."""
    if not path.is_file():
        return set()
    content = path.read_text(encoding="utf-8")
    try:
        import tomllib  # Python 3.11+

        data = tomllib.loads(content)
        project = data.get("project", {})
        dependencies = project.get("dependencies", []) if isinstance(project, dict) else []
        optional = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
        values = list(dependencies) if isinstance(dependencies, list) else []
        if isinstance(optional, dict):
            values.extend(dep for group in optional.values() if isinstance(group, list) for dep in group)
        names: set[str] = set()
        for value in values:
            if isinstance(value, str):
                match = PACKAGE_NAME.match(value.strip())
                if match:
                    names.add(match.group(1))
        return names
    except (ImportError, ValueError):
        # Minimal Python 3.10 fallback for PEP 621 dependency arrays.
        names: set[str] = set()
        section = ""
        in_array = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                section = stripped
                in_array = False
                continue
            if section not in {"[project]", "[project.optional-dependencies]"}:
                continue
            if not in_array and re.match(r"[A-Za-z0-9_-]+\s*=\s*\[", stripped):
                in_array = True
                stripped = stripped.split("[", 1)[1]
            if in_array:
                for value in re.findall(r"""["']([^"']+)["']""", stripped):
                    match = PACKAGE_NAME.match(value.strip())
                    if match:
                        names.add(match.group(1))
                if "]" in stripped:
                    in_array = False
        return names


def declared_dependencies(root: Path) -> list[str]:
    names = parse_requirements(root / "requirements.txt")
    names.update(parse_pyproject(root / "pyproject.toml"))
    return sorted(names, key=str.casefold)


def distribution_license(name: str) -> str:
    try:
        dist = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ValueError(f"license metadata not found for declared dependency {name!r}; install it to verify") from exc

    metadata = dist.metadata
    expression = metadata.get("License-Expression")
    if expression and expression.strip():
        return expression.strip()
    license_value = metadata.get("License")
    classifiers = metadata.get_all("Classifier") or []
    license_classifiers = [
        item.partition("::")[-1].strip()
        for item in classifiers
        if item.startswith("License ::")
    ]
    pieces = [item for item in [license_value, *license_classifiers] if item and item.strip()]
    return " / ".join(dict.fromkeys(pieces)) if pieces else "UNKNOWN"


def check(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    rows: list[tuple[str, str]] = []
    errors: list[str] = []
    for name in declared_dependencies(root):
        try:
            license_name = distribution_license(name)
        except ValueError as exc:
            rows.append((name, "UNVERIFIED"))
            errors.append(str(exc))
            continue
        rows.append((name, license_name))
        if license_name == "UNKNOWN":
            errors.append(f"license metadata is missing for declared dependency {name!r}")
        elif FORBIDDEN.search(license_name):
            errors.append(f"prohibited license detected for {name!r}: {license_name}")
    return rows, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root")
    args = parser.parse_args(argv)
    try:
        rows, errors = check(args.root.resolve())
    except (OSError, UnicodeError) as exc:
        print(f"License check error: {exc}", file=sys.stderr)
        return 1

    print("Declared Python dependency licenses:")
    if not rows:
        print("  No dependencies declared in requirements.txt or pyproject.toml.")
    for name, license_name in rows:
        print(f"  {name}: {license_name}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("License check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
