#!/usr/bin/env python3
"""Offline inventory check only; this does not launch Claude Code."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".claude" / "manifest.json"


def main() -> int:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            raise ValueError("unsupported manifest schema")
        inventory = manifest["inventory"]
        discovered: dict[str, list[Path]] = {}
        for kind, spec in inventory.items():
            folder = (ROOT / spec["directory"]).resolve()
            folder.relative_to(ROOT.resolve())
            paths = sorted(folder.glob(spec["pattern"])) if folder.is_dir() else []
            discovered[kind] = paths
            missing = sorted(set(spec.get("required", [])) - {path.name for path in paths})
            if missing:
                raise ValueError(f"{kind} missing required entries: {', '.join(missing)}")
            if kind in ("agents", "skills") and len(paths) < spec["minimum_count"]:
                raise ValueError(f"{kind}: found {len(paths)}, minimum is {spec['minimum_count']}")
            for path in paths:
                if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                    raise ValueError(f"Empty or invalid file: {path.relative_to(ROOT)}")
        print("OFFLINE INVENTORY CHECK PASS (not Claude Code runtime discovery)")
        for kind, paths in discovered.items():
            print(f"{kind}: {len(paths)} files")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"OFFLINE INVENTORY CHECK FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
