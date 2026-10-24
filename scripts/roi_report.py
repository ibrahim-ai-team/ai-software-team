#!/usr/bin/env python3
"""Generate a local Markdown ROI report from one sprint's JSON metrics."""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / ".claude" / "metrics"


class MetricsError(ValueError):
    """Raised when a metrics file is invalid."""


def positive_number(value: Any, field: str, story_id: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MetricsError(f"story {story_id!r}: {field} must be a number")
    if not math.isfinite(value) or value < 0:
        raise MetricsError(f"story {story_id!r}: {field} must be a finite non-negative number")
    return float(value)


def load_stories(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise MetricsError(f"metrics file not found: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MetricsError(f"cannot read valid JSON from {path}: {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("stories"), list):
        raise MetricsError("input JSON must be an object containing a 'stories' array")

    stories = data["stories"]
    for index, story in enumerate(stories):
        if not isinstance(story, dict):
            raise MetricsError(f"stories[{index}] must be a JSON object")
        story_id = story.get("story_id")
        if not isinstance(story_id, str) or not story_id.strip():
            raise MetricsError(f"stories[{index}].story_id must be a non-empty string")
        for field in ("agent_minutes", "tokens", "human_hours_estimated"):
            positive_number(story.get(field), field, story_id)
    return stories


def build_report(sprint: int, stories: list[dict[str, Any]], rate_hourly: float, token_cost: float) -> str:
    lines = [
        f"# Sprint {sprint} — ROI report",
        "",
        "| Story ID | Agent time (min) | Tokens | Token cost ($) | Estimated human hours | Estimated human cost ($) | ROI ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not stories:
        lines.extend(["| — | — | — | — | — | — | — |", "", "Aucune story"])
    else:
        for story in stories:
            minutes = float(story["agent_minutes"])
            tokens = float(story["tokens"])
            human_hours = float(story["human_hours_estimated"])
            agent_cost = tokens * token_cost
            human_cost = human_hours * rate_hourly
            ratio = ("∞" if human_cost > 0 else "0.00") if agent_cost == 0 else f"{human_cost / agent_cost:.2f}"
            lines.append(
                f"| {story['story_id'].strip()} | {minutes:g} | {tokens:g} | "
                f"{agent_cost:.6f} | {human_hours:g} | {human_cost:.2f} | {ratio} |"
            )

    lines.extend(
        [
            "",
            "## Méthode",
            "",
            f"- Coût tokens ($) = tokens × {token_cost:g} $/token.",
            f"- Coût humain estimé ($) = heures-homme estimées × {rate_hourly:g} $/heure.",
            "- Ratio ROI = coût humain estimé ÷ coût tokens. Un ratio supérieur à 1 signifie que le coût humain estimé dépasse le coût tokens mesuré.",
            "- Le temps agent est reporté en minutes, sans être ajouté au coût tokens. Le ratio n'inclut pas les autres coûts d'infrastructure.",
            "- Les coûts tokens sont arrondis à 6 décimales, les coûts humains à 2 décimales et le ratio à 2 décimales. Si le coût tokens est nul, le ratio vaut ∞ si le coût humain est positif, sinon 0.00.",
            f"- Source locale : .claude/metrics/sprint-{sprint}.json. Aucun appel réseau.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprint", required=True, type=int, help="sprint number (positive integer)")
    parser.add_argument("--rate-hourly", type=float, default=80.0, help="estimated human hourly rate in dollars (default: 80)")
    parser.add_argument("--token-cost", type=float, default=0.000003, help="cost per token in dollars (default: 0.000003)")
    args = parser.parse_args(argv)
    if args.sprint <= 0:
        parser.error("--sprint must be a positive integer")
    for name in ("rate_hourly", "token_cost"):
        value = getattr(args, name)
        if not math.isfinite(value) or value < 0:
            parser.error(f"--{name.replace('_', '-')} must be a finite non-negative number")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = METRICS_DIR / f"sprint-{args.sprint}.json"
    try:
        stories = load_stories(path)
        print(build_report(args.sprint, stories, args.rate_hourly, args.token_cost))
    except MetricsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
