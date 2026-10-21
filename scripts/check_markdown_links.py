#!/usr/bin/env python3
"""Check repository-relative Markdown links without network access."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def find_broken_links(root: Path) -> list[str]:
    errors: list[str] = []
    for source in sorted(root.rglob("*.md")):
        if any(part in {".git", ".venv", "node_modules"} for part in source.parts):
            continue
        try:
            content = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{source.relative_to(root)}: cannot read Markdown: {exc}")
            continue
        for line_number, line in enumerate(content.splitlines(), 1):
            for match in LINK.finditer(line):
                target = match.group(1).strip().split()[0].strip("<>")
                if not target or target.startswith(("https://", "http://", "mailto:", "tel:", "data:")):
                    continue
                target = target.split("#", 1)[0].split("?", 1)[0]
                if not target:
                    continue
                candidate = (source.parent / target).resolve()
                try:
                    candidate.relative_to(root.resolve())
                except ValueError:
                    errors.append(f"{source.relative_to(root)}:{line_number}: link escapes repository: {target}")
                    continue
                if not candidate.exists():
                    errors.append(f"{source.relative_to(root)}:{line_number}: missing local link: {target}")
    return errors


if __name__ == "__main__":
    failures = find_broken_links(ROOT)
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print("Markdown local-link check passed.")
