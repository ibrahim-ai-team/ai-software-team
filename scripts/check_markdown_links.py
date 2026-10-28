#!/usr/bin/env python3
"""Check repository-relative Markdown links without network access."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
# Backticked references such as `workflows/sprint-governance.md#release-criteria`, which agents follow.
CODE_ANCHOR = re.compile(r"`([A-Za-z0-9_./-]+\.md)#([A-Za-z0-9_-]+)`")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")


def github_slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation removed, spaces become hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        match = None if in_fence else HEADING.match(line)
        if match:
            slug = github_slug(match.group(1))
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def find_broken_links(root: Path) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}

    def check_anchor(where: str, target: Path, anchor: str) -> None:
        if target.suffix != ".md":
            return
        if target not in anchor_cache:
            anchor_cache[target] = heading_anchors(target)
        if anchor not in anchor_cache[target]:
            errors.append(f"{where}: missing heading anchor: {target.relative_to(root.resolve())}#{anchor}")

    for source in sorted(root.rglob("*.md")):
        if any(part in {".git", ".venv", "node_modules"} for part in source.parts):
            continue
        try:
            content = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{source.relative_to(root)}: cannot read Markdown: {exc}")
            continue
        for line_number, line in enumerate(content.splitlines(), 1):
            where = f"{source.relative_to(root)}:{line_number}"
            for match in LINK.finditer(line):
                target = match.group(1).strip().split()[0].strip("<>")
                if not target or target.startswith(("https://", "http://", "mailto:", "tel:", "data:")):
                    continue
                path_part, _, anchor = target.partition("#")
                path_part = path_part.split("?", 1)[0]
                if not path_part:
                    if anchor:
                        check_anchor(where, source.resolve(), anchor)
                    continue
                candidate = (source.parent / path_part).resolve()
                try:
                    candidate.relative_to(root.resolve())
                except ValueError:
                    errors.append(f"{where}: link escapes repository: {path_part}")
                    continue
                if not candidate.exists():
                    errors.append(f"{where}: missing local link: {path_part}")
                elif anchor:
                    check_anchor(where, candidate, anchor)
            for match in CODE_ANCHOR.finditer(line):
                # Repository-root paths first, then paths relative to the file.
                path_part, anchor = match.groups()
                candidate = next(
                    (c for c in ((root / path_part).resolve(), (source.parent / path_part).resolve()) if c.is_file()), None
                )
                if candidate is None:
                    errors.append(f"{where}: missing referenced file: {path_part}")
                else:
                    check_anchor(where, candidate, anchor)
    return errors


if __name__ == "__main__":
    failures = find_broken_links(ROOT)
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print("Markdown local-link check passed.")
