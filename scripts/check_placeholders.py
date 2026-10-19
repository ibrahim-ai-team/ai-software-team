#!/usr/bin/env python3
"""Flag unresolved placeholder field values in planning artifacts.

Templates legitimately contain placeholders, so `templates/` is skipped. A
placeholder is reported only when it is a field value ("Owner: TBD", a table
cell "| TBD |"). Per workflows/backlog-quality-gates.md, a TBD that cites an
issue (#12) or a date (2026-11-01) is an explicit, tracked deferral and passes.

Usage: check_placeholders.py [path ...]   (default: the repository root)
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", "templates"}
PLACEHOLDER = re.compile(r"(?:^|:\**|\|)\s*\**(TBD|TBC|TODO|FIXME)\**\s*(?:\||$|[.;,(—-])", re.IGNORECASE)
TRACKED = re.compile(r"#\d+|\b\d{4}-\d{2}-\d{2}\b")


def markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        candidates = [path] if path.is_file() else sorted(path.rglob("*.md"))
        for candidate in candidates:
            if candidate.suffix == ".md" and not SKIP_DIRS & set(candidate.parts):
                files.append(candidate)
    return files


def find_placeholders(paths: list[Path], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for source in markdown_files(paths):
        try:
            lines = source.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(f"{source}: cannot read Markdown: {exc}")
            continue
        in_code = False
        for line_number, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or TRACKED.search(line):
                continue
            match = PLACEHOLDER.search(line)
            if match:
                try:
                    shown = source.resolve().relative_to(root.resolve())
                except ValueError:
                    shown = source
                errors.append(f"{shown}:{line_number}: unresolved placeholder '{match.group(1)}': {line.strip()}")
    return errors


if __name__ == "__main__":
    targets = [Path(arg) for arg in sys.argv[1:]] or [ROOT]
    failures = find_placeholders(targets)
    if failures:
        print("\n".join(failures))
        print("Resolve the value, or defer it explicitly with an issue reference or date.")
        sys.exit(1)
    print("Placeholder check passed.")
