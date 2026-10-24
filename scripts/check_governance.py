#!/usr/bin/env python3
"""Check sprint records, release criteria and PR bodies against the governance rules.

Offline, read-only checks of the records described in
workflows/sprint-governance.md. They verify that a record is complete and
internally consistent; they do not query GitHub, so a passing check does not
prove that GitHub Issues, milestones or Project fields match the record.

Usage:
  check_governance.py [--as-of YYYY-MM-DD] SPRINT_RECORD.md [...]
  check_governance.py --state PROJECT_STATE.md --repo DIR [--release]
  check_governance.py --pr-body PR_BODY.md

Exit status: 0 when no error was found, 1 when an error was found, 2 on usage error.
"""

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

SPRINT_ID = re.compile(r"^S\d+$")
ISSUE_REF = re.compile(r"#\d+|https://github\.com/[^\s/]+/[^\s/]+/(?:pull|issues)/\d+")
OPEN_STATUSES = {"ready", "in progress", "in review", "blocked"}
CLOSE_STATUSES = {"done", "not done", "blocked", "cancelled"}
ALL_STATUSES = OPEN_STATUSES | CLOSE_STATUSES
WEAK_EVIDENCE = {"", "-", "tbd", "n/a", "agent reported", "reported by agent", "claimed", "pr opened", "pr open"}
CREATION_RESULTS = re.compile(r"^(new|subtask of #\d+|duplicate of #\d+|rejected)$")
EMPTY = {"", "-", "none", "tbd", "n/a"}
# Workflow inputs that let a release skip its own criteria (for example
# `accept_below_release_thresholds`). Matched against workflow input keys.
BYPASS_INPUT = re.compile(
    r"^\s+([a-z0-9_]*(?:accept|allow|skip|bypass|ignore|override)[a-z0-9_]*"
    r"(?:threshold|gate|check|criteria)[a-z0-9_]*)\s*:",
    re.IGNORECASE,
)


def sections(text: str) -> dict[str, list[tuple[int, str]]]:
    """Map each lower-cased `##` heading to its (line number, line) pairs."""
    result: dict[str, list[tuple[int, str]]] = {}
    current = ""
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            current = line[3:].strip().lower()
            result.setdefault(current, [])
        elif current:
            result[current].append((number, line))
    return result


def fields(lines: list[tuple[int, str]]) -> dict[str, str]:
    """Parse `- Key: value` bullet lines."""
    found: dict[str, str] = {}
    for _, line in lines:
        match = re.match(r"^\s*-\s*([^:]+):\s*(.*)$", line)
        if match:
            found[match.group(1).strip().lower()] = match.group(2).strip()
    return found


def table(lines: list[tuple[int, str]]) -> list[tuple[int, dict[str, str]]]:
    """Parse the first Markdown table in a section, keyed by lower-cased header."""
    header: list[str] = []
    rows: list[tuple[int, dict[str, str]]] = []
    for number, line in lines:
        if not line.strip().startswith("|"):
            if header:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not header:
            header = [cell.lower() for cell in cells]
        elif not all(set(cell) <= set("-: ") for cell in cells):
            rows.append((number, dict(zip(header, cells, strict=False))))
    return rows


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def is_empty(value: str) -> bool:
    return value.strip().strip("`").lower() in EMPTY


class SprintRecord:
    def __init__(self, path: Path):
        self.path = path
        parts = sections(path.read_text(encoding="utf-8"))
        self.info = fields(parts.get("sprint", []))
        self.committed = table(parts.get("committed issues", []))
        self.changes = table(parts.get("scope changes", []))
        self.created = table(parts.get("issue creation log", []))
        self.review = fields(parts.get("sprint review", []))
        self.sprint_id = self.info.get("sprint id", "")
        self.status = self.info.get("status", "").lower()
        self.start = parse_date(self.info.get("start", ""))
        self.end = parse_date(self.info.get("end", ""))

    def issues(self) -> dict[str, dict[str, str]]:
        return {row.get("issue", ""): row for _, row in self.committed}


def check_sprint(record: SprintRecord, as_of: dt.date) -> list[str]:
    errors: list[str] = []
    where = str(record.path)

    def err(code: str, message: str, line: int | None = None) -> None:
        errors.append(f"{where}{f':{line}' if line else ''}: {code} {message}")

    if not SPRINT_ID.match(record.sprint_id):
        err("G01", f"Sprint ID must look like S1, S2, ... (got '{record.sprint_id}')")
    if record.start is None or record.end is None:
        err("G03", "Start and End must be real ISO dates (YYYY-MM-DD); do not invent or leave TBD")
    elif record.end < record.start:
        err("G03", "End must not be before Start")
    if is_empty(record.info.get("goal", "")):
        err("G04", "one measurable sprint goal is required")
    if record.status not in {"planned", "active", "closed"}:
        err("G05", f"Status must be Planned, Active or Closed (got '{record.status}')")
    approved = record.info.get("approved by", "")
    if record.status in {"active", "closed"} and (is_empty(approved) or "not approved" in approved.lower()):
        err("G05", "an Active or Closed sprint needs 'Approved by' (decision ID, who, date)")
    if is_empty(record.info.get("membership source", "")):
        err("G06", "Membership source is required (milestone, Project iteration field, or 'this file only')")

    changes = {row.get("id", ""): (line, row) for line, row in record.changes}
    for line, row in record.changes:
        if is_empty(row.get("displaces", "")):
            err("G07", f"scope change {row.get('id', '')} must say what it displaces (or 'nothing: within capacity')", line)

    points = 0
    for line, row in record.committed:
        issue, status = row.get("issue", ""), row.get("status", "").lower()
        if not ISSUE_REF.search(issue):
            err("G02", f"committed item '{issue}' must reference a GitHub issue (#n)", line)
        if status not in ALL_STATUSES:
            err("G08", f"{issue}: unknown status '{row.get('status', '')}'", line)
        added = row.get("added by", "").strip()
        if added.lower() != "plan":
            change = changes.get(added)
            if change is None:
                err("G07", f"{issue} was added by '{added}', not by the approved plan or a recorded scope change", line)
            elif change[1].get("decision", "").lower() != "approved" or is_empty(change[1].get("decided by", "")):
                err("G07", f"{issue}: scope change {added} is not approved by a named decision owner", line)
        try:
            points += int(row.get("points", "0") or 0)
        except ValueError:
            err("G15", f"{issue}: Points must be a whole number", line)
        if status == "done":
            evidence = row.get("evidence", "")
            if not ISSUE_REF.search(row.get("pr", "")) or "merged" not in evidence.lower():
                err("G08", f"{issue}: Done needs the merged PR and evidence that says 'merged' (an opened PR is not Done)", line)
            elif evidence.strip().lower() in WEAK_EVIDENCE:
                err("G08", f"{issue}: '{evidence}' is not completion evidence", line)
        if status == "blocked" and is_empty(row.get("next", "")):
            err("G09", f"{issue}: a Blocked item needs a next action and owner in Next", line)
        if record.status == "closed":
            if status not in CLOSE_STATUSES:
                err("G11", f"{issue}: a Closed sprint accounts for every item as Done, Not done, Blocked or Cancelled", line)
            elif status != "done" and is_empty(row.get("next", "")):
                err(
                    "G11",
                    f"{issue}: incomplete or cancelled work needs a disposition in Next (backlog, candidate for next sprint, or reason)",
                    line,
                )

    capacity = record.info.get("capacity (points)", "")
    if capacity.isdigit() and points > int(capacity):
        err("G15", f"committed points {points} exceed capacity {capacity}; displace work through a scope change instead")
    elif not capacity.isdigit():
        err("G15", "Capacity (points) must be a whole number")

    if record.status == "active" and record.end and as_of > record.end:
        err(
            "G10", f"sprint ended {record.end.isoformat()} and is still Active on {as_of.isoformat()}: close it, do not extend it"
        )
    if record.status == "closed":
        if record.review.get("goal met", "").lower() not in {"yes", "partial", "no"}:
            err("G11", "Sprint review must state 'Goal met: yes | partial | no'")
        if is_empty(record.review.get("evidence", "")):
            err("G11", "Sprint review must link the evidence for the goal assessment")

    committed = record.issues()
    for line, row in record.created:
        result = row.get("result", "").strip().lower()
        issue = row.get("issue", "").strip()
        if is_empty(row.get("duplicate search", "")):
            err("G12", f"issue creation '{issue}' has no recorded duplicate search", line)
        if not CREATION_RESULTS.match(result):
            err("G12", f"Result must be new, subtask of #n, duplicate of #n or rejected (got '{row.get('result', '')}')", line)
        elif result.startswith(("duplicate", "rejected")) and ISSUE_REF.search(issue):
            err("G12", f"{issue} was created although its own check says '{result}'; link the existing issue instead", line)
        if is_empty(row.get("problem", "")):
            err("G12", f"issue creation '{issue}' needs the problem it solves", line)
        if ISSUE_REF.search(issue) and is_empty(row.get("why now", "")):
            err("G12", f"{issue} needs a reason for creating it now rather than later", line)
        target = row.get("target", "").strip()
        if target == record.sprint_id and ISSUE_REF.search(issue) and issue not in committed:
            err(
                "G12",
                f"{issue} targets {target} but is not in Committed issues; record a scope change or target the backlog",
                line,
            )
    return errors


def check_sprints(paths: list[Path], as_of: dt.date) -> list[str]:
    records = [SprintRecord(path) for path in paths]
    errors = [error for record in records for error in check_sprint(record, as_of)]
    seen: dict[str, Path] = {}
    for record in records:
        if record.sprint_id in seen:
            errors.append(f"{record.path}: G01 Sprint ID {record.sprint_id} is also used by {seen[record.sprint_id]}")
        seen[record.sprint_id] = record.path
    ordered = sorted((r for r in records if SPRINT_ID.match(r.sprint_id)), key=lambda r: int(r.sprint_id[1:]))
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.status in {"active", "closed"} and previous.status != "closed":
            errors.append(f"{current.path}: G14 {current.sprint_id} cannot start while {previous.sprint_id} is not Closed")
        if previous.end and current.start and current.start <= previous.end:
            errors.append(f"{current.path}: G14 {current.sprint_id} starts before {previous.sprint_id} ends")
    return errors


def check_release(state: Path, repo: Path, release: bool) -> tuple[list[str], list[str]]:
    """Return (errors, notes). Mirrors are `path: text with {value}`, separated by ';'."""
    parts = sections(state.read_text(encoding="utf-8"))
    criteria = table(parts.get("release criteria", []))
    conflicts = table(parts.get("requirement conflicts", []))
    open_conflicts = {row.get("criterion", "") for _, row in conflicts if row.get("status", "").lower() != "resolved"}
    errors: list[str] = []
    notes: list[str] = []
    if not criteria:
        errors.append(f"{state}: G20 no Release criteria table; record the approved criteria in one place")
    for line, row in criteria:
        name, value = row.get("criterion", ""), row.get("value", "")
        where = f"{state}:{line}: {row.get('id', '')} {name}"
        if not value.isdigit():
            errors.append(f"{where}: G20 Value must be a whole number")
            continue
        if is_empty(row.get("decision", "")):
            errors.append(f"{where}: G20 the criterion needs the decision ID that approved it")
        for mirror in filter(None, (m.strip() for m in row.get("mirrors", "").split(";"))):
            if is_empty(mirror):
                continue
            path_text, _, pattern = mirror.partition(":")
            target = repo / path_text.strip().strip("`")
            if "{value}" not in pattern or not target.is_file():
                errors.append(f"{where}: G21 mirror '{mirror}' must be 'path: text with {{value}}' and the file must exist")
                continue
            regex = r"\s*".join(map(re.escape, pattern.strip().strip("`").split())).replace(re.escape("{value}"), r"(\d+)")
            match = re.search(regex, target.read_text(encoding="utf-8"))
            if match is None:
                errors.append(f"{where}: G21 mirror text not found in {path_text.strip()}")
            elif match.group(1) != value:
                message = f"{where}: G21 approved value {value} but {path_text.strip()} says {match.group(1)}"
                if name in open_conflicts:
                    (errors if release else notes).append(f"{message} (open conflict recorded; release blocked until decided)")
                else:
                    errors.append(f"{message}: unrecorded requirement conflict; record it and ask the decision owner")
    if release:
        for name in sorted(open_conflicts):
            errors.append(f"{state}: G22 open requirement conflict on '{name}' blocks the release")
        workflows = repo / ".github" / "workflows"
        for workflow in sorted(workflows.glob("*.y*ml")) if workflows.is_dir() else []:
            for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
                match = BYPASS_INPUT.match(line)
                if match:
                    errors.append(
                        f"{workflow}:{number}: G22 release bypass '{match.group(1)}'; "
                        "releases must meet the approved criteria, not override them"
                    )
    return errors, notes


def check_pr_body(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not re.search(r"(?im)^\s*(closes|fixes|resolves|refs|part of)\s+#\d+", text):
        errors.append(f"{path}: G30 link the issue with 'Closes #n' or 'Refs #n'")
    sprint = re.search(r"(?im)^\s*-?\s*sprint:\s*(\S.*)$", text)
    if sprint is None or not (SPRINT_ID.match(sprint.group(1).strip()) or sprint.group(1).strip().lower() == "none"):
        errors.append(f"{path}: G30 state 'Sprint: S<n>' (or 'Sprint: none' for work outside a sprint)")
    if "validation evidence" not in text.lower():
        errors.append(f"{path}: G30 a 'Validation evidence' section is required")
    if not re.search(r"(?i)human owner will perform the final merge", text):
        errors.append(f"{path}: G31 keep the statement that the human owner performs the final merge")
    if re.search(r"(?i)\bauto-?merge (is )?enabled\b|\benable(d)? auto-?merge\b", text):
        errors.append(f"{path}: G31 agents must not enable auto-merge")
    return errors


def check_design_handoff(path: Path) -> list[str]:
    """Validate a design handoff copied from the repository template."""
    parts = sections(path.read_text(encoding="utf-8"))
    raw: dict[str, str] = {}
    for section_lines in parts.values():
        raw.update(fields(section_lines))

    aliases = {
        "story": ("story", "user story"),
        "decision": ("decision",),
        "artifact": ("artifact", "artifact url or repository path"),
        "acceptance criteria": (
            "acceptance criteria",
            "acceptance criteria covered",
        ),
        "approved by": ("approved by",),
        "approval status": ("approval status",),
        "approval evidence": ("approval evidence",),
        "qa verification": (
            "qa verification",
            "qa verification scope",
            "test evidence link(s)",
        ),
        "exception rationale": (
            "exception rationale",
            "figma exception rationale (if applicable)",
        ),
    }
    data: dict[str, str] = {}
    for canonical, names in aliases.items():
        for name in names:
            if raw.get(name, "").strip():
                data[canonical] = raw[name].strip()
                break

    errors: list[str] = []

    def present(value: str) -> bool:
        cleaned = value.strip().strip("`").lower()
        return (
            cleaned not in EMPTY
            and not (cleaned.startswith("<") and cleaned.endswith(">"))
            and not (cleaned.startswith("[") and cleaned.endswith("]"))
        )

    for key, message in {
        "story": "link the relevant User Story",
        "decision": "Decision must be required or exception",
        "acceptance criteria": "map the design to story acceptance criteria",
        "approved by": "record the design approver",
        "approval status": "record Approval status as approved",
        "approval evidence": "link or describe durable approval evidence",
        "qa verification": "record QA verification scope or N/A rationale",
    }.items():
        if not present(data.get(key, "")):
            errors.append(f"{path}: D01 {message}")

    approval_status = data.get("approval status", "").strip().lower()
    if present(approval_status) and approval_status != "approved":
        errors.append(
            f"{path}: D01 Approval status must be approved before frontend work"
        )

    story = data.get("story", "")
    if present(story) and not ISSUE_REF.search(story):
        errors.append(f"{path}: D01 Story must contain a GitHub issue reference or URL")

    decision = data.get("decision", "").strip().lower()
    if present(decision) and decision not in {"required", "exception"}:
        errors.append(f"{path}: D01 Decision must be required or exception")

    artifact = data.get("artifact", "").strip()
    if decision == "required" and not present(artifact):
        errors.append(f"{path}: D01 a required design gate needs a design artifact")
    if present(artifact) and (
        artifact.lower() in {"tbd", "n/a", "none", "to be added", "-"}
        or "<" in artifact
        or ">" in artifact
        or not (
            artifact.startswith("https://")
            or artifact.startswith("http://")
            or "/" in artifact
        )
    ):
        errors.append(
            f"{path}: D01 Artifact must be a real URL or traceable repository path, not a placeholder"
        )

    rationale = data.get("exception rationale", "")
    if decision == "exception" and not present(rationale):
        errors.append(
            f"{path}: D01 an exception requires a documented no-material-design-impact rationale"
        )
    if decision == "exception" and present(rationale):
        normalized = rationale.lower()
        if "no" not in normalized and "not" not in normalized and "minor" not in normalized:
            errors.append(
                f"{path}: D01 exception rationale must explain why no material design artifact is needed"
            )
    evidence = data.get("approval evidence", "")
    if not present(evidence):
        errors.append(f"{path}: D01 approval evidence must not be a placeholder")
    elif not (evidence.startswith("https://") or ISSUE_REF.search(evidence)):
        errors.append(
            f"{path}: D01 approval evidence must link to a GitHub issue/PR or durable decision URL"
        )
    return errors


def check_frontend_readiness(handoff: Path | None) -> list[str]:
    """Fail closed when frontend work has no approved design handoff record."""
    if handoff is None:
        return ["D02 frontend work is blocked: provide an approved design handoff record"]
    return check_design_handoff(handoff)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sprints", nargs="*", type=Path, help="sprint record files")
    parser.add_argument("--as-of", type=parse_date, default=dt.date.today(), help="date used for the end-date check")
    parser.add_argument("--state", type=Path, help="project state file with Release criteria")
    parser.add_argument("--repo", type=Path, default=Path("."), help="repository root for release mirrors")
    parser.add_argument("--release", action="store_true", help="fail on open conflicts and release bypass inputs")
    parser.add_argument("--pr-body", type=Path, help="pull request body to check")
    parser.add_argument("--design-handoff", type=Path, help="design handoff record to validate")
    parser.add_argument(
        "--frontend-readiness", action="store_true", help="fail closed unless the supplied design handoff is valid"
    )
    args = parser.parse_args(argv)
    if args.as_of is None and args.sprints:
        parser.error("--as-of must be YYYY-MM-DD when validating sprint records")
    if not (args.sprints or args.state or args.pr_body or args.design_handoff or args.frontend_readiness):
        parser.print_usage()
        return 2
    errors: list[str] = []
    notes: list[str] = []
    if args.sprints:
        errors += check_sprints(args.sprints, args.as_of)
    if args.state:
        release_errors, notes = check_release(args.state, args.repo, args.release)
        errors += release_errors
    if args.pr_body:
        errors += check_pr_body(args.pr_body)
    if args.frontend_readiness:
        errors += check_frontend_readiness(args.design_handoff)
    elif args.design_handoff:
        errors += check_design_handoff(args.design_handoff)
    for note in notes:
        print(f"NOTE {note}")
    if errors:
        print("\n".join(errors))
        return 1
    print("Governance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
