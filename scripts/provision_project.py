#!/usr/bin/env python3
"""Plan, validate and idempotently provision an application project workspace on GitHub.

The team produces a project plan (see templates/project-plan.example.json). This script:
  plan  <plan.json>            validate the plan, assign the next project ID if needed, print the
                               repository tree and the plan digest the sponsor approves.
  apply <plan.json> [--dry-run] create or reuse repositories, scaffolds (as bootstrap PRs), labels,
                               milestones, issues, dependency links and the Project board, recording
                               every step in a state file. Re-running never duplicates resources.

GitHub calls go through a client object. `GhClient` uses the authenticated `gh` CLI of the person
running it; tests use an in-memory fake. Nothing here reads or prints tokens.
"""

from __future__ import annotations

import argparse
import base64
import copy
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ID_RE = re.compile(r"^idea-\d{2,}$")
SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
RESERVED_SLUGS = {"ai-software-team", "github", "idea"}
TAG_RE = re.compile(r"\[ai-team:(idea-\d+)\]")
ROLE_RE = re.compile(r"^[a-z][a-z0-9-]{0,29}$")
OWNER_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")
STYLES = {"single-repo", "monolith", "frontend-backend", "services"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
TYPES = {"epic", "story", "task", "bug", "qa"}
COORDINATION_ROLE = "management"
APP_TOPIC = "ai-team-app"
BOOTSTRAP_BRANCH = "bootstrap/initial-structure"
REQUIRED_CHECK_NOTE = "Add the repository's CI check names once its CI exists."
MAX_RETRIES = 2
RETRY_DELAYS = (5, 20)  # seconds; secondary rate limits need longer than a second

# Permission the person running the provisioner needs for each operation (shown on 401/403/404).
PERMISSIONS = {
    "list_repos": "read access to the organization's repositories",
    "create_repo": "permission to create repositories in the organization (org owner, or members allowed "
    "to create repositories); token scope `repo` (classic) or fine-grained Administration: write",
    "topics": "repository Administration: write (or admin role) to set topics",
    "contents": "repository Contents: write to create the bootstrap branch and files",
    "pulls": "repository Pull requests: write to open the bootstrap PR",
    "labels": "repository Issues: write to create labels",
    "milestones": "repository Issues: write to create milestones",
    "issues": "repository Issues: write to create and update issues",
    "protection": "repository Administration: write (admin role) to configure branch protection",
    "project": "organization Projects: read and write; token scope `project` (classic) or fine-grained "
    "organization Projects: write",
}


class PlanError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


class GitHubError(Exception):
    def __init__(self, status: int | None, message: str):
        super().__init__(f"HTTP {status}: {message}" if status else message)
        self.status = status


class PermissionDenied(GitHubError):
    pass


class TransientError(GitHubError):
    pass


TOKEN_RE = re.compile(r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")


def redact(text: str) -> str:
    return TOKEN_RE.sub("[redacted]", text)


NETWORK_RE = re.compile(r"connect|timed? ?out|timeout|EOF|TLS|temporar|reset by peer", re.IGNORECASE)


def classify(status: int | None, message: str) -> GitHubError:
    message = redact(message)
    if status == 403 and "rate limit" in message.lower():
        return TransientError(status, message)  # secondary rate limits are reported as 403
    if status in (401, 403):
        return PermissionDenied(status, message)
    if status == 429 or (status is not None and status >= 500):
        return TransientError(status, message)
    if status is None and NETWORK_RE.search(message):
        return TransientError(status, message)
    return GitHubError(status, message)


# ---------------------------------------------------------------- planning


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _repo_project_ids(repo) -> set[str]:
    """Project IDs a repository belongs to, from its description tag, topics or a legacy idea-NN- name."""
    if isinstance(repo, str):
        repo = {"name": repo}
    ids = set(TAG_RE.findall(repo.get("description") or ""))
    ids |= {t for t in repo.get("topics") or [] if ID_RE.match(t)}
    if m := re.match(r"^(idea-\d+)-", repo.get("name", "")):
        ids.add(m.group(1))
    return ids


def next_project_id(existing_repos: list) -> str:
    numbers = [int(i.split("-")[1]) for r in existing_repos for i in _repo_project_ids(r)]
    return f"idea-{(max(numbers) + 1 if numbers else 1):02d}"


def default_roles(architecture: dict) -> list[str]:
    style = architecture.get("style")
    if style in ("single-repo", "monolith"):
        return ["app"]
    if style == "frontend-backend":
        return ["front", "back"]
    if style == "services":
        roles = ["front"] if architecture.get("has_frontend") else []
        return roles + [str(s) for s in architecture.get("services", [])]
    return []


APPROVALS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "approvals"
APPROVERS_PATH = APPROVALS_DIR.parent / "human-approvers.json"


def human_approval_problem(approvals_dir: Path, project_id: str, digest: str) -> str | None:
    """Why the human approval record for this plan is missing or invalid, or None when it is valid.

    The plan file's own approval block can be edited by whoever writes the plan; this record lives
    where agents cannot write (`.claude/approvals/`, denied in settings and agent scopes).
    """
    path = approvals_dir / f"PROVISION-{project_id}.json"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return f"the sponsor must create {path} with approved_by and plan_digest = {digest}"
    except (OSError, UnicodeError, json.JSONDecodeError):
        return f"{path} is unreadable or not valid JSON"
    if not isinstance(record, dict) or record.get("plan_digest") != digest:
        return f"{path} does not approve this plan (plan_digest must be {digest})"
    approved_by = record.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by.strip():
        return f"{path} needs a non-empty approved_by"
    try:
        approvers = json.loads(APPROVERS_PATH.read_text(encoding="utf-8")).get("approvers")
    except FileNotFoundError:
        return None  # no approver list configured yet
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
        return f"{APPROVERS_PATH} is unreadable or malformed"
    names = {n.strip().casefold() for n in approvers if isinstance(n, str)} if isinstance(approvers, list) else set()
    if approved_by.strip().casefold() not in names:
        return f"{approved_by} is not listed in {APPROVERS_PATH}"
    return None


def plan_digest(plan: dict) -> str:
    """Digest of the normalized plan without its approval block; the sponsor approves this value."""
    body = {k: v for k, v in plan.items() if k not in ("approval", "repos", "home_role")}
    # Full SHA-256: a truncated digest would let a second plan be found with the same value.
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def validate_plan(raw: dict, existing_repos: list | None = None) -> dict:
    """Return a normalized copy of the plan or raise PlanError with every problem found."""
    plan = copy.deepcopy(raw)
    errors: list[str] = []
    org = plan.setdefault("organization", "ibrahim-ai-team")
    if not OWNER_RE.match(str(org)):
        errors.append("organization must be a GitHub organization login")
    project = plan.get("project") or {}
    if not project.get("id") and existing_repos is not None:
        project["id"] = next_project_id(existing_repos)
    pid = project.get("id", "")
    if not ID_RE.match(pid):
        errors.append(f"project.id '{pid}' must look like idea-01 (or run plan with --check-github to assign one)")
    if not str(project.get("name", "")).strip():
        errors.append("project.name (the app name the sponsor proposed or confirmed, e.g. Shopinow) is required")
    project["slug"] = slug = project.get("slug") or slugify(str(project.get("name", "")))
    if not (SLUG_RE.match(slug) and len(slug) <= 40) or slug in RESERVED_SLUGS or ID_RE.match(slug):
        errors.append(
            f"project.slug '{slug}' must be lowercase words joined by '-', max 40 characters, not reserved and not an idea-NN ID"
        )
    for repo in existing_repos or []:
        name = repo if isinstance(repo, str) else repo.get("name", "")
        owners = _repo_project_ids(repo)
        if name.startswith(slug + "-") and owners and pid not in owners:
            errors.append(f"app name '{slug}' is already used by {', '.join(sorted(owners))} ({name}); choose another name")
    if not OWNER_RE.match(str(plan.get("owner", ""))):
        errors.append("owner must be the GitHub username of the human who merges PRs")
    if plan.get("visibility", "private") not in ("private", "public", "internal"):
        errors.append("visibility must be private, public or internal")
    plan["visibility"] = plan.get("visibility", "private")
    arch = plan.get("architecture") or {}
    if arch.get("style") not in STYLES:
        errors.append(f"architecture.style must be one of {sorted(STYLES)}")
    if not str(arch.get("decision", "")).strip():
        errors.append("architecture.decision (the ADR summary and trade-offs) is required")

    specs = {r.get("role"): r for r in plan.get("repositories", []) if isinstance(r, dict)}
    roles = list(specs) if specs else default_roles(arch)
    if arch.get("style") == "services" and not [r for r in roles if r != "front"]:
        errors.append("architecture.style 'services' needs at least one service in architecture.services")
    coordination = plan.get("coordination_repo", "auto")
    if coordination == "auto":
        coordination = len(roles) > 1
    if COORDINATION_ROLE in roles:
        errors.append(f"role '{COORDINATION_ROLE}' is reserved for the coordination repository")
    repos = []
    for role in ([COORDINATION_ROLE] if coordination else []) + roles:
        spec = specs.get(role, {})
        if not ROLE_RE.match(str(role)):
            errors.append(f"repository role '{role}' must be lowercase letters, digits or '-' (max 30)")
            continue
        repo = {
            "role": role,
            "name": f"{slug}-{role}",
            "coordination": role == COORDINATION_ROLE,
            "purpose": spec.get("purpose")
            or ("Project coordination: requirements, ADRs, backlog and status" if role == COORDINATION_ROLE else ""),
            "stack": spec.get("stack", ""),
            "testing": spec.get("testing", ""),
            "setup": spec.get("setup", ""),
        }
        if not repo["coordination"]:
            for key in ("purpose", "stack", "testing"):
                if not str(repo[key]).strip():
                    errors.append(f"repositories[{role}].{key} is required before a repository may be created")
        repos.append(repo)
    if len({r["name"] for r in repos}) != len(repos):
        errors.append("repository roles must be unique")
    if not repos:
        errors.append("no repositories derived from the plan")
    home = repos[0]["role"] if repos else ""  # coordination repo, or the only app repo

    sprint = plan.setdefault("sprint", {})
    sprint.setdefault("length_days", 14)
    sprint.setdefault("count", 1)
    length = sprint["length_days"]
    if not (isinstance(length, int) and not isinstance(length, bool) and 1 <= length <= 28):
        errors.append("sprint.length_days must be an integer from 1 to 28")
    try:
        dt.date.fromisoformat(str(sprint.get("start", "")))
    except ValueError:
        errors.append("sprint.start must be a date YYYY-MM-DD")
    if not (isinstance(sprint["count"], int) and 1 <= sprint["count"] <= 6):
        errors.append("sprint.count must be 1-6")

    keys: dict[str, dict] = {}
    for item in plan.get("backlog", []):
        key = str(item.get("key", ""))
        if not re.match(r"^[A-Z][A-Z0-9]*-\d+$", key):
            errors.append(f"backlog key '{key}' must look like US-1")
            continue
        if key in keys:
            errors.append(f"backlog key '{key}' is duplicated")
        keys[key] = item
        item.setdefault("repo", home)
        item.setdefault("type", "story")
        item.setdefault("priority", "P2")
        item.setdefault("depends_on", [])
        if item["repo"] not in {r["role"] for r in repos}:
            errors.append(f"{key}: repo '{item['repo']}' is not in the repository plan")
        if item["type"] not in TYPES:
            errors.append(f"{key}: type must be one of {sorted(TYPES)}")
        if item["priority"] not in PRIORITIES:
            errors.append(f"{key}: priority must be P0-P3")
        if not str(item.get("title", "")).strip():
            errors.append(f"{key}: title is required")
        if item["type"] in ("story", "task", "qa") and not item.get("acceptance_criteria"):
            errors.append(f"{key}: acceptance_criteria are required")
        if "sprint" in item and not (isinstance(item["sprint"], int) and 1 <= item["sprint"] <= sprint["count"]):
            errors.append(f"{key}: sprint must be between 1 and sprint.count")
    for key, item in keys.items():
        for dep in item["depends_on"]:
            if dep not in keys:
                errors.append(f"{key}: depends_on '{dep}' is not a backlog key")
    if not errors:
        errors += _cycles(keys)
    if not keys:
        errors.append("backlog must contain at least one item")
    if errors:
        raise PlanError(errors)
    plan["project"] = project
    plan["repos"] = repos
    plan["home_role"] = home
    return plan


def _cycles(keys: dict[str, dict]) -> list[str]:
    state: dict[str, int] = {}

    def visit(k: str, path: list[str]) -> str | None:
        if state.get(k) == 1:
            return " -> ".join(path + [k])
        if state.get(k) == 2:
            return None
        state[k] = 1
        for d in keys[k]["depends_on"]:
            if cycle := visit(d, path + [k]):
                return cycle
        state[k] = 2
        return None

    for k in keys:
        if cycle := visit(k, []):
            return [f"dependency cycle: {cycle}"]
    return []


def render_tree(plan: dict, with_files: bool = True) -> str:
    pid, org = plan["project"]["id"], plan["organization"]
    lines = [
        f"{org}/  (GitHub organization; repositories cannot be nested, so the 'apps' grouping is",
        f"        the app-name prefix + topics '{APP_TOPIC}', '{pid}' + one Project board)",
        f'└── {plan["project"]["slug"]}  "{plan["project"]["name"]}" (project {pid})  '
        f"[{plan['architecture']['style']}, {plan['visibility']}]",
    ]
    for i, repo in enumerate(plan["repos"]):
        last = i == len(plan["repos"]) - 1
        lines.append(f"    {'└──' if last else '├──'} {repo['name']}  — {repo['purpose']}")
        pad = "    " if last else "│   "
        for f in scaffold_files(plan, repo) if with_files else []:
            lines.append(f"    {pad}    {f}")
    counts: dict[str, int] = {}
    for item in plan["backlog"]:
        counts[item["repo"]] = counts.get(item["repo"], 0) + 1
    lines.append(f'    GitHub Project: "{project_title(plan)}" linking {len(plan["repos"])} repositories')
    lines.append("    Issues: " + ", ".join(f"{plan['project']['slug']}-{r}: {n}" for r, n in counts.items()))
    lines.append(f"    Milestones: {plan['sprint']['count']} x {plan['sprint']['length_days']}-day sprint(s) per repository")
    return "\n".join(lines)


def project_title(plan: dict) -> str:
    return f"{plan['project']['name']} ({plan['project']['id']})"


def repo_tag(plan: dict) -> str:
    return f"[ai-team:{plan['project']['id']}]"


# ---------------------------------------------------------------- scaffold content


def scaffold_files(plan: dict, repo: dict) -> dict[str, str]:
    pid, org, name = plan["project"]["id"], plan["organization"], plan["project"]["name"]
    links = "\n".join(f"| [`{r['name']}`](https://github.com/{org}/{r['name']}) | {r['purpose']} |" for r in plan["repos"])
    home = next(r for r in plan["repos"] if r["role"] == plan["home_role"])
    readme = [
        f"# {repo['name']}",
        "",
        f"Part of **{name}** (project `{pid}`). {repo['purpose']}.",
        "",
        "## Project repositories",
        "",
        "| Repository | Purpose |",
        "|---|---|",
        links,
        "",
        f"Planning and status live in [`{home['name']}`](https://github.com/{org}/{home['name']}) and the "
        f'GitHub Project "{project_title(plan)}". Issues carry the label `project:{pid}`.',
        "",
    ]
    if not repo["coordination"]:
        readme += [
            "## Development",
            "",
            f"Stack: {repo['stack']}.",
            "",
            repo["setup"] or "Setup steps are added with the first implementation story.",
            "",
            "## Testing",
            "",
            repo["testing"],
            "",
        ]
    files = {
        "README.md": "\n".join(readme),
        "CONTRIBUTING.md": (
            f"# Contributing\n\nWork on a feature branch and open a pull request. Link the issue "
            f"(`Closes #n`). CI must pass. Only @{plan['owner']} merges pull requests. Agents "
            f"never push to `main` or merge. Sprints are {plan['sprint']['length_days']} days.\n"
        ),
        "SECURITY.md": (
            f"# Security\n\nReport vulnerabilities privately to @{plan['owner']}; do not open a public "
            "issue. Never commit secrets, tokens or credentials; use the platform's secret store.\n"
        ),
        ".github/CODEOWNERS": f"* @{plan['owner']}\n",
        ".github/pull_request_template.md": (
            "## Summary\n\n## Linked issue\nCloses #\n\n## Tests run\n| Check | "
            "Result |\n|---|---|\n\n## Human merge\n- [ ] Owner reviews and merges\n"
        ),
    }
    if repo["role"] == plan["home_role"]:
        files["docs/requirements.md"] = "# Requirements\n\n" + "\n".join(f"- {r}" for r in plan.get("requirements", [])) + "\n"
        files["docs/adr/0001-architecture.md"] = (
            f"# ADR-0001: {plan['architecture']['style']} architecture\n\n"
            f"Status: Accepted by @{plan['owner']} via plan approval\n\n"
            f"{plan['architecture']['decision']}\n"
        )
        files["docs/repository-plan.md"] = "# Repository plan\n\n```\n" + render_tree(plan, with_files=False) + "\n```\n"
        files["docs/project-plan.json"] = (
            json.dumps({k: v for k, v in plan.items() if k not in ("repos", "home_role")}, indent=2, sort_keys=True) + "\n"
        )
        files["docs/project-state.md"] = (
            f"# Project state — {name} ({pid})\n\nCurrent phase: BACKLOG_READY (workspace provisioned from the "
            f"approved plan).\nSprint length: {plan['sprint']['length_days']} days, first sprint starts "
            f"{plan['sprint']['start']}.\n\n## Repositories\n\n"
            + "\n".join(f"- {r['name']}: {r['purpose']}" for r in plan["repos"])
            + "\n\n## Next action\n\nOwner merges the bootstrap PRs; then `agile-orchestrator` runs `/plan-sprint`.\n"
            "See `docs/provisioning-report.md` for created resources and manual steps.\n"
        )
    return files


def _strip_keys(text: str) -> str:
    """Remove ai-team-key markers from free text so one backlog item cannot claim another's issue."""
    return re.sub(r"<!--\s*ai-team-key:.*?-->", "", text, flags=re.DOTALL)


def issue_body(plan: dict, item: dict, resolved: dict[str, str]) -> str:
    deps = [f"- Depends on: {resolved.get(d, d + ' (link pending)')}" for d in item["depends_on"]] or ["- None"]
    criteria = [f"- [ ] {_strip_keys(str(c))}" for c in item.get("acceptance_criteria", [])] or ["- Not applicable"]
    sprint = f" · Sprint: {item['sprint']}" if "sprint" in item else ""
    return (
        "\n".join(
            [
                _strip_keys(item.get("description", "")).strip(),
                "",
                "## Acceptance criteria",
                *criteria,
                "",
                "## Dependencies",
                *deps,
                "",
                f"Project: {plan['project']['id']} · Priority: {item['priority']}{sprint}",
                f"<!-- ai-team-key: {plan['project']['id']}/{item['key']} -->",
            ]
        ).lstrip()
        + "\n"
    )


KEY_RE = re.compile(r"<!-- ai-team-key: (idea-\d+)/([A-Z][A-Z0-9]*-\d+) -->")


# ---------------------------------------------------------------- provisioning engine


class Provisioner:
    def __init__(self, client, plan: dict, state_path: Path, sleep=time.sleep, dry_run: bool = False):
        self.gh, self.plan, self.path, self.sleep, self.dry_run = client, plan, state_path, sleep, dry_run
        self.org, self.pid, self.slug = plan["organization"], plan["project"]["id"], plan["project"]["slug"]
        self.state = {
            "project_id": self.pid,
            "plan_digest": plan_digest(plan),
            "dry_run": dry_run,
            "phase": "PROVISIONING",
            "steps": {},
            "resources": {},
            "manual_actions": [],
            "started_at": _now(),
        }
        self.issues: dict[str, dict] = {}

    # -- bookkeeping
    def _save(self) -> None:
        self.state["updated_at"] = _now()
        if not self.dry_run:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.state, indent=2) + "\n", encoding="utf-8")

    def step(self, step_id: str, op: str, fn, needs: tuple[str, ...] = ()) -> str:
        blocked = [
            n for n in needs if self.state["steps"].get(n, {}).get("status") not in ("CREATED", "EXISTS", "UPDATED", "DRY_RUN")
        ]
        if blocked:
            return self._record(step_id, "SKIPPED_DEPENDENCY", f"waiting on {', '.join(blocked)}")
        for attempt in range(MAX_RETRIES + 1):
            try:
                status, detail = fn()
                return self._record(step_id, "DRY_RUN" if self.dry_run and status != "EXISTS" else status, detail)
            except TransientError as exc:
                if attempt == MAX_RETRIES:
                    return self._record(step_id, "FAILED", f"{exc} (after {MAX_RETRIES} retries)")
                self.sleep(RETRY_DELAYS[attempt])
            except PermissionDenied as exc:
                return self._record(step_id, "PERMISSION_DENIED", f"{exc}. Needed: {PERMISSIONS[op]}")
            except GitHubError as exc:
                return self._record(step_id, "FAILED", str(exc))
            except Exception as exc:  # never leave the state stuck in PROVISIONING
                return self._record(step_id, "FAILED", redact(f"unexpected {type(exc).__name__}: {exc}"))
        return "FAILED"  # unreachable

    def _record(self, step_id: str, status: str, detail: str) -> str:
        self.state["steps"][step_id] = {"status": status, "detail": detail, "at": _now()}
        self._save()
        return status

    def manual(self, text: str) -> None:
        if text not in self.state["manual_actions"]:
            self.state["manual_actions"].append(text)

    # -- run
    def run(self) -> dict:
        self._save()
        conflicts = self.step("preflight", "list_repos", self.preflight)
        if conflicts != "EXISTS":
            self.state["phase"] = "BLOCKED"
            self._save()
            return self.state
        for repo in self.plan["repos"]:
            r = f"repo:{repo['name']}"
            self.step(r, "create_repo", lambda repo=repo: self.ensure_repo(repo))
            self.step(f"topics:{repo['name']}", "topics", lambda repo=repo: self.ensure_topics(repo), (r,))
            self.step(f"labels:{repo['name']}", "labels", lambda repo=repo: self.ensure_labels(repo), (r,))
            self.step(f"milestones:{repo['name']}", "milestones", lambda repo=repo: self.ensure_milestones(repo), (r,))
            self.step(f"scaffold:{repo['name']}", "contents", lambda repo=repo: self.ensure_scaffold(repo), (r,))
            self.step(f"pr:{repo['name']}", "pulls", lambda repo=repo: self.ensure_pr(repo), (f"scaffold:{repo['name']}",))
            if self.plan.get("options", {}).get("branch_protection"):
                self.step(f"protection:{repo['name']}", "protection", lambda repo=repo: self.protect(repo), (r,))
            else:
                self.manual(
                    f"Protect `main` in {repo['name']}: require a PR and the repository's CI checks, "
                    "disallow bypass and force-push (plan option branch_protection was not approved)."
                )
        for item in self.plan["backlog"]:
            name = self.repo_name(item["repo"])
            self.step(
                f"issue:{item['key']}",
                "issues",
                lambda item=item: self.ensure_issue(item),
                (f"labels:{name}", f"milestones:{name}"),
            )
        for item in self.plan["backlog"]:
            if item["depends_on"]:
                self.step(
                    f"deps:{item['key']}", "issues", lambda item=item: self.link_dependencies(item), (f"issue:{item['key']}",)
                )
        if self.plan.get("options", {}).get("project_board", True):
            self.step("project", "project", self.ensure_project, tuple(f"repo:{r['name']}" for r in self.plan["repos"]))
        self.manual(
            "Align the Project's Status options with workflows/project-status-transitions.md "
            "(Backlog, Ready, In Progress, In Review, Changes Requested, Approved — Awaiting Human Merge, "
            "Blocked, Done) and enable the Project workflows 'Item closed → Done' and 'Auto-add'."
        )
        self.manual("Review and merge each bootstrap PR (branch bootstrap/initial-structure); agents do not merge.")
        self._set_phase()
        self.step("report", "contents", self.write_report, (f"scaffold:{self.repo_name(self.plan['home_role'])}",))
        self._set_phase()
        self._save()
        return self.state

    def _set_phase(self) -> None:
        statuses = {s["status"] for s in self.state["steps"].values()}
        if statuses & {"FAILED", "PERMISSION_DENIED", "SKIPPED_DEPENDENCY"}:
            phase = "PARTIAL"
        else:
            phase = "COMPLETE_WITH_MANUAL_STEPS" if self.state["manual_actions"] else "COMPLETE"
        self.state["phase"] = ("DRY_RUN_" if self.dry_run else "") + phase

    def repo_name(self, role: str) -> str:
        return f"{self.slug}-{role}"

    # -- steps (each returns (status, detail))
    def preflight(self):
        foreign = []
        for repo in self.plan["repos"]:
            existing = self.gh.get_repo(self.org, repo["name"])
            if existing and repo_tag(self.plan) not in (existing.get("description") or ""):
                foreign.append(repo["name"])
        if foreign:
            raise GitHubError(
                409,
                f"repositories already exist but were not created for {self.pid}: "
                f"{', '.join(foreign)}. Choose another project ID; nothing was changed.",
            )
        return "EXISTS", "no conflicting repositories"

    def ensure_repo(self, repo):
        url = f"https://github.com/{self.org}/{repo['name']}"
        self.state["resources"][repo["name"]] = url
        if self.gh.get_repo(self.org, repo["name"]):
            return "EXISTS", url
        if not self.dry_run:
            self.gh.create_repo(self.org, repo["name"], f"{repo['purpose']} {repo_tag(self.plan)}", self.plan["visibility"])
        return "CREATED", url

    def ensure_topics(self, repo):
        wanted = sorted({APP_TOPIC, self.pid, repo["role"]})
        current = set(self.gh.get_topics(self.org, repo["name"])) if self.gh.get_repo(self.org, repo["name"]) else set()
        if set(wanted) <= current:
            return "EXISTS", ", ".join(wanted)
        if not self.dry_run:
            self.gh.set_topics(self.org, repo["name"], sorted(current | set(wanted)))
        return "UPDATED", ", ".join(wanted)

    def labels_for(self, role):
        items = [i for i in self.plan["backlog"] if i["repo"] == role]
        return {f"project:{self.pid}"} | {f"type:{i['type']}" for i in items} | {f"priority:{i['priority']}" for i in items}

    def ensure_labels(self, repo):
        existing = self.gh.list_labels(self.org, repo["name"]) if self.gh.get_repo(self.org, repo["name"]) else set()
        missing = sorted(self.labels_for(repo["role"]) - existing)
        for label in missing:
            if not self.dry_run:
                try:
                    self.gh.create_label(self.org, repo["name"], label, "1d76db" if label.startswith("project:") else "ededed")
                except GitHubError as exc:
                    if not (exc.status == 422 and "already_exists" in str(exc)):
                        raise
        return ("CREATED" if missing else "EXISTS"), f"{len(missing)} created"

    def milestone_titles(self):
        start = dt.date.fromisoformat(self.plan["sprint"]["start"])
        days = self.plan["sprint"]["length_days"]
        return {n: (f"Sprint {n}", start + dt.timedelta(days=days * n - 1)) for n in range(1, self.plan["sprint"]["count"] + 1)}

    def ensure_milestones(self, repo):
        existing = self.gh.list_milestones(self.org, repo["name"]) if self.gh.get_repo(self.org, repo["name"]) else {}
        created = 0
        for title, due in self.milestone_titles().values():
            if title not in existing and not self.dry_run:
                self.gh.create_milestone(self.org, repo["name"], title, due.isoformat() + "T23:59:59Z")
                created += 1
            elif title not in existing:
                created += 1
        return ("CREATED" if created else "EXISTS"), f"{created} created"

    def ensure_scaffold(self, repo):
        if self.dry_run and not self.gh.get_repo(self.org, repo["name"]):
            return "CREATED", f"{len(scaffold_files(self.plan, repo))} files on {BOOTSTRAP_BRANCH}"
        name = repo["name"]
        if self.gh.get_ref_sha(self.org, name, BOOTSTRAP_BRANCH) is None:
            base = self.gh.get_repo(self.org, name).get("default_branch", "main")
            sha = self.gh.get_ref_sha(self.org, name, base)
            if sha is None:
                raise TransientError(409, f"{name} has no commit on {base} yet (just created?)")
            if not self.dry_run:
                self.gh.create_ref(self.org, name, BOOTSTRAP_BRANCH, sha)
        written = 0
        for path, text in scaffold_files(self.plan, repo).items():
            current = self.gh.get_file(self.org, name, path, BOOTSTRAP_BRANCH)
            if current and current[0] == text:
                continue
            if not self.dry_run:
                self.gh.put_file(
                    self.org,
                    name,
                    path,
                    BOOTSTRAP_BRANCH,
                    text,
                    f"chore: bootstrap {path} for {self.pid}",
                    current[1] if current else None,
                )
            written += 1
        return ("UPDATED" if written else "EXISTS"), f"{written} file(s) written to {BOOTSTRAP_BRANCH}"

    def ensure_pr(self, repo):
        if self.dry_run and not self.gh.get_repo(self.org, repo["name"]):
            return "CREATED", "bootstrap PR"
        existing = self.gh.find_pr(self.org, repo["name"], BOOTSTRAP_BRANCH)
        if existing:
            return "EXISTS", existing["html_url"]
        if self.dry_run:
            return "CREATED", "bootstrap PR"
        base = (self.gh.get_repo(self.org, repo["name"]) or {}).get("default_branch", "main")
        pr = self.gh.create_pr(
            self.org,
            repo["name"],
            BOOTSTRAP_BRANCH,
            base,
            f"Bootstrap {repo['name']} for {self.pid}",
            f"Initial structure generated from the approved {self.pid} plan. "
            f"Review and merge is reserved for @{self.plan['owner']}.",
        )
        return "CREATED", pr["html_url"]

    def protect(self, repo):
        if not self.dry_run:
            branch = (self.gh.get_repo(self.org, repo["name"]) or {}).get("default_branch", "main")
            self.gh.protect_branch(self.org, repo["name"], branch)
        self.manual(f"{REQUIRED_CHECK_NOTE} ({repo['name']})")
        return "UPDATED", "PR required, no bypass, no force-push or deletion"

    def find_issue(self, item):
        name = self.repo_name(item["repo"])
        for issue in self.gh.list_issues(self.org, name, f"project:{self.pid}"):
            m = KEY_RE.search(issue.get("body") or "")
            if m and m.group(1) == self.pid and m.group(2) == item["key"]:
                return issue
        return None

    def ensure_issue(self, item):
        name = self.repo_name(item["repo"])
        if self.dry_run and not self.gh.get_repo(self.org, name):
            self.issues[item["key"]] = {"html_url": f"{name}#(new)", "number": 0, "node_id": ""}
            return "CREATED", f"{name}: {item['title']}"
        existing = self.find_issue(item)
        if existing:
            self.issues[item["key"]] = existing
            return "EXISTS", existing["html_url"]
        if self.dry_run:
            self.issues[item["key"]] = {"html_url": f"{name}#(new)", "number": 0, "node_id": ""}
            return "CREATED", f"{name}: {item['title']}"
        milestone = None
        if "sprint" in item:
            milestone = self.gh.list_milestones(self.org, name).get(self.milestone_titles()[item["sprint"]][0])
        labels = [f"project:{self.pid}", f"type:{item['type']}", f"priority:{item['priority']}"]
        issue = self.gh.create_issue(
            self.org, name, f"[{item['key']}] {item['title']}", issue_body(self.plan, item, {}), labels, milestone
        )
        self.issues[item["key"]] = issue
        return "CREATED", issue["html_url"]

    def link_dependencies(self, item):
        resolved = {d: self.issues[d]["html_url"] for d in item["depends_on"] if d in self.issues}
        body = issue_body(self.plan, item, resolved)
        issue = self.issues[item["key"]]
        changed = issue.get("body") != body
        if changed and not self.dry_run:
            self.gh.update_issue_body(self.org, self.repo_name(item["repo"]), issue["number"], body)
            issue["body"] = body
        pending = [d for d in item["depends_on"] if d not in resolved]
        if pending:  # the dependency issue does not exist yet; a rerun links it
            return "SKIPPED_DEPENDENCY", f"link pending for {', '.join(pending)}"
        return ("UPDATED" if changed else "EXISTS"), f"{len(resolved)} dependency link(s)"

    def ensure_project(self):
        title = project_title(self.plan)
        project = self.gh.find_project(self.org, title)
        status = "EXISTS"
        if project and repo_tag(self.plan) not in (project.get("description") or ""):
            raise GitHubError(
                409,
                f"a Project titled '{title}' exists but was not created for {self.pid} "
                f"(no {repo_tag(self.plan)} in its description); not adopting it",
            )
        if not project:
            if self.dry_run:
                return "CREATED", f"project '{title}'"
            project = self.gh.create_project(self.org, title, f"{self.plan['project']['name']} {repo_tag(self.plan)}")
            status = "CREATED"
        self.state["resources"]["project"] = project.get("url", title)
        for repo in self.plan["repos"]:
            if repo["name"] not in project.get("repos", set()) and not self.dry_run:
                self.gh.link_project_repo(project["id"], self.org, repo["name"])
                status = "UPDATED" if status == "EXISTS" else status
        for issue in self.issues.values():
            if issue.get("node_id") and issue["node_id"] not in project.get("items", set()) and not self.dry_run:
                self.gh.add_project_item(project["id"], issue["node_id"])
                status = "UPDATED" if status == "EXISTS" else status
        if "Sprint" not in project.get("fields", set()) and not self.dry_run:
            try:
                self.gh.create_iteration_field(
                    project["id"], "Sprint", self.plan["sprint"]["start"], self.plan["sprint"]["length_days"]
                )
            except GitHubError as exc:
                self.manual(
                    f"Add an iteration field 'Sprint' ({self.plan['sprint']['length_days']} days from "
                    f"{self.plan['sprint']['start']}) to the Project; the API call failed: {exc}"
                )
        return status, project.get("url", title)

    def write_report(self):
        home = next(r for r in self.plan["repos"] if r["role"] == self.plan["home_role"])
        lines = [
            f"# Provisioning report — {self.pid}",
            "",
            f"Phase: {self.state['phase']}.",
            "",
            "| Step | Status | Detail |",
            "|---|---|---|",
        ]
        lines += [f"| {k} | {v['status']} | {v['detail']} |" for k, v in self.state["steps"].items()]
        lines += ["", "## Manual actions", *[f"- [ ] {m}" for m in self.state["manual_actions"]], ""]
        text = "\n".join(lines)
        if self.dry_run:
            return "CREATED", "docs/provisioning-report.md"
        pr = self.gh.find_pr(self.org, home["name"], BOOTSTRAP_BRANCH)
        if pr and pr.get("state", "open") != "open":
            self.manual(f"The bootstrap PR in {home['name']} is closed; the latest report is only in {self.path}.")
            return "EXISTS", "bootstrap PR closed; report kept in the local state file"
        current = self.gh.get_file(self.org, home["name"], "docs/provisioning-report.md", BOOTSTRAP_BRANCH)
        if current and current[0] == text:
            return "EXISTS", "report unchanged"
        self.gh.put_file(
            self.org,
            home["name"],
            "docs/provisioning-report.md",
            BOOTSTRAP_BRANCH,
            text,
            f"docs: provisioning report for {self.pid}",
            current[1] if current else None,
        )
        return "UPDATED", f"{home['name']}:{BOOTSTRAP_BRANCH}/docs/provisioning-report.md"


class DryRunClient:
    """Read-only proxy: lets `apply --dry-run` read real GitHub state while refusing every write."""

    WRITES = {
        "create_repo",
        "set_topics",
        "create_ref",
        "put_file",
        "create_pr",
        "create_label",
        "create_milestone",
        "create_issue",
        "update_issue_body",
        "protect_branch",
        "create_project",
        "link_project_repo",
        "add_project_item",
        "create_iteration_field",
    }

    def __init__(self, inner):
        self.inner = inner

    def __getattr__(self, name):
        if name in self.WRITES:
            raise RuntimeError(f"dry run attempted a write: {name}")
        return getattr(self.inner, name)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- real client (gh CLI)


class GhClient:
    """GitHub operations through the caller's authenticated `gh` CLI. Not exercised by unit tests."""

    GRAPHQL_STATUS = {"FORBIDDEN": 403, "INSUFFICIENT_SCOPES": 403, "NOT_FOUND": 404, "RATE_LIMITED": 429}

    def _run(self, args: list[str], body=None):
        try:
            proc = subprocess.run(
                ["gh", *args], input=json.dumps(body) if body is not None else None, capture_output=True, text=True, check=False
            )
        except FileNotFoundError:
            raise GitHubError(None, "the gh CLI is not installed; install it and run `gh auth login`") from None
        if proc.returncode != 0:
            m = re.search(r"HTTP (\d{3})", proc.stderr)
            status = int(m.group(1)) if m else None
            message = proc.stderr.strip()
            try:  # GraphQL failures put the error list on stdout without an HTTP status
                errors = json.loads(proc.stdout).get("errors") or []
            except (ValueError, AttributeError):
                errors = []
            if errors:
                status = status or next(
                    (self.GRAPHQL_STATUS[e["type"]] for e in errors if e.get("type") in self.GRAPHQL_STATUS), 422
                )
                message = "; ".join(e.get("message", "") for e in errors)
            # Redact before truncating so a token cut at the limit cannot escape the pattern.
            raise classify(status, redact(message)[:300])
        return proc.stdout

    def _api(self, method: str, path: str, body=None):
        out = self._run(["api", "-X", method, path, *(["--input", "-"] if body is not None else [])], body)
        return json.loads(out) if out.strip() else None

    def _list(self, path: str) -> list:
        out = self._run(["api", "--paginate", path, "--jq", ".[]"])
        return [json.loads(line) for line in out.splitlines() if line.strip()]

    def _graphql(self, query: str, **variables):
        args = ["api", "graphql", "-f", f"query={query}"]
        for k, v in variables.items():
            args += ["-F" if isinstance(v, int) else "-f", f"{k}={v}"]
        data = json.loads(self._run(args))
        if data.get("errors"):
            msg = "; ".join(e.get("message", "") for e in data["errors"])
            raise classify(403 if "permission" in msg.lower() or "access" in msg.lower() else 422, msg)
        return data["data"]

    def list_org_repos(self, org):
        return [
            {"name": r["name"], "description": r.get("description") or "", "topics": r.get("topics") or []}
            for r in self._list(f"orgs/{org}/repos?per_page=100&type=all")
        ]

    def get_repo(self, org, name):
        try:
            return self._api("GET", f"repos/{org}/{name}")
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise

    def create_repo(self, org, name, description, visibility):
        return self._api(
            "POST", f"orgs/{org}/repos", {"name": name, "description": description, "visibility": visibility, "auto_init": True}
        )

    def get_topics(self, org, name):
        return self._api("GET", f"repos/{org}/{name}/topics")["names"]

    def set_topics(self, org, name, topics):
        self._api("PUT", f"repos/{org}/{name}/topics", {"names": topics})

    def get_ref_sha(self, org, name, branch):
        try:
            return self._api("GET", f"repos/{org}/{name}/git/ref/heads/{branch}")["object"]["sha"]
        except GitHubError as exc:
            if exc.status in (404, 409):
                return None
            raise

    def create_ref(self, org, name, branch, sha):
        self._api("POST", f"repos/{org}/{name}/git/refs", {"ref": f"refs/heads/{branch}", "sha": sha})

    def get_file(self, org, name, path, ref):
        try:
            data = self._api("GET", f"repos/{org}/{name}/contents/{path}?ref={ref}")
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise
        return base64.b64decode(data["content"]).decode("utf-8"), data["sha"]

    def put_file(self, org, name, path, branch, text, message, sha=None):
        body = {"message": message, "branch": branch, "content": base64.b64encode(text.encode()).decode()}
        if sha:
            body["sha"] = sha
        self._api("PUT", f"repos/{org}/{name}/contents/{path}", body)

    def find_pr(self, org, name, head):
        prs = self._list(f"repos/{org}/{name}/pulls?state=all&head={org}:{head}")
        return prs[0] if prs else None

    def create_pr(self, org, name, head, base, title, body):
        return self._api("POST", f"repos/{org}/{name}/pulls", {"head": head, "base": base, "title": title, "body": body})

    def list_labels(self, org, name):
        return {label["name"] for label in self._list(f"repos/{org}/{name}/labels?per_page=100")}

    def create_label(self, org, name, label, color):
        self._api("POST", f"repos/{org}/{name}/labels", {"name": label, "color": color})

    def list_milestones(self, org, name):
        return {m["title"]: m["number"] for m in self._list(f"repos/{org}/{name}/milestones?state=all&per_page=100")}

    def create_milestone(self, org, name, title, due_on):
        return self._api("POST", f"repos/{org}/{name}/milestones", {"title": title, "due_on": due_on})["number"]

    def list_issues(self, org, name, label):
        return [
            i for i in self._list(f"repos/{org}/{name}/issues?state=all&per_page=100&labels={label}") if "pull_request" not in i
        ]

    def create_issue(self, org, name, title, body, labels, milestone):
        payload = {"title": title, "body": body, "labels": labels}
        if milestone:
            payload["milestone"] = milestone
        return self._api("POST", f"repos/{org}/{name}/issues", payload)

    def update_issue_body(self, org, name, number, body):
        self._api("PATCH", f"repos/{org}/{name}/issues/{number}", {"body": body})

    def protect_branch(self, org, name, branch):
        self._api(
            "PUT",
            f"repos/{org}/{name}/branches/{branch}/protection",
            {
                "required_status_checks": None,
                "enforce_admins": True,
                "restrictions": None,
                "required_pull_request_reviews": {"required_approving_review_count": 0},
                "allow_force_pushes": False,
                "allow_deletions": False,
            },
        )

    def find_project(self, org, title):
        q = (
            "query($login:String!,$q:String!){organization(login:$login){projectsV2(first:20,query:$q){nodes{"
            "id url title shortDescription repositories(first:50){nodes{name}} fields(first:50){nodes{... on ProjectV2FieldCommon{name}}}"
            " items(first:100){nodes{content{... on Issue{id}}}}}}}}"
        )
        nodes = self._graphql(q, login=org, q=title)["organization"]["projectsV2"]["nodes"]
        for p in nodes:
            if p["title"] == title:
                return {
                    "id": p["id"],
                    "url": p["url"],
                    "description": p.get("shortDescription") or "",
                    "repos": {r["name"] for r in p["repositories"]["nodes"]},
                    "fields": {f.get("name") for f in p["fields"]["nodes"]},
                    "items": {(i.get("content") or {}).get("id") for i in p["items"]["nodes"]},
                }
        return None

    def create_project(self, org, title, description):
        owner = self._graphql("query($login:String!){organization(login:$login){id}}", login=org)["organization"]["id"]
        p = self._graphql(
            "mutation($o:ID!,$t:String!){createProjectV2(input:{ownerId:$o,title:$t}){projectV2{id url}}}", o=owner, t=title
        )["createProjectV2"]["projectV2"]
        self._graphql(
            "mutation($p:ID!,$d:String!){updateProjectV2(input:{projectId:$p,shortDescription:$d}){projectV2{id}}}",
            p=p["id"],
            d=description,
        )
        return {"id": p["id"], "url": p["url"], "description": description, "repos": set(), "fields": set(), "items": set()}

    def link_project_repo(self, project_id, org, name):
        repo_id = self.get_repo(org, name)["node_id"]
        self._graphql(
            "mutation($p:ID!,$r:ID!){linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r}){repository{id}}}",
            p=project_id,
            r=repo_id,
        )

    def add_project_item(self, project_id, content_id):
        self._graphql(
            "mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}",
            p=project_id,
            c=content_id,
        )

    def create_iteration_field(self, project_id, name, start, days):
        self._graphql(
            "mutation($p:ID!,$n:String!,$s:Date!,$d:Int!){createProjectV2Field(input:{projectId:$p,"
            "dataType:ITERATION,name:$n,iterationConfiguration:{startDate:$s,duration:$d,iterations:[]}})"
            "{projectV2Field{... on ProjectV2IterationField{id}}}}",
            p=project_id,
            n=name,
            s=start,
            d=days,
        )


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None, client=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_plan = sub.add_parser("plan", help="validate the plan and print the repository tree")
    p_plan.add_argument("plan")
    p_plan.add_argument("--check-github", action="store_true", help="read existing repos to assign the next ID")
    p_apply = sub.add_parser("apply", help="provision the approved plan (idempotent)")
    p_apply.add_argument("plan")
    p_apply.add_argument("--dry-run", action="store_true", help="read GitHub, write nothing")
    p_apply.add_argument("--state-dir", default=".provisioning")
    p_apply.add_argument("--approvals-dir", default=str(APPROVALS_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    raw = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    gh = client or GhClient()
    try:
        existing = (
            gh.list_org_repos(raw.get("organization", "ibrahim-ai-team"))
            if (args.command == "plan" and args.check_github)
            else None
        )
        plan = validate_plan(raw, existing)
    except PlanError as exc:
        print("Plan is invalid:\n" + "\n".join(f"- {e}" for e in exc.errors))
        return 2
    except PermissionDenied as exc:
        print(f"Cannot read organization repositories: {exc}. Needed: {PERMISSIONS['list_repos']}")
        return 3
    digest = plan_digest(plan)
    if args.command == "plan":
        print(render_tree(plan))
        print(f"\nPlan digest: {digest}  (record it in approval.plan_digest after the sponsor approves)")
        return 0
    approval = raw.get("approval") or {}
    if not args.dry_run and not (approval.get("approved_by") and approval.get("plan_digest") == digest):
        print(
            f"Refusing to provision: the plan needs sponsor approval with approval.plan_digest = {digest} "
            "(the digest changes whenever the plan changes)."
        )
        return 4
    if not args.dry_run and (problem := human_approval_problem(Path(args.approvals_dir), plan["project"]["id"], digest)):
        print(f"Refusing to provision: {problem}")
        return 4
    state_path = Path(args.state_dir) / f"{plan['project']['id']}.json"
    state = Provisioner(DryRunClient(gh) if args.dry_run else gh, plan, state_path, dry_run=args.dry_run).run()
    print(
        json.dumps(
            {
                "phase": state["phase"],
                "steps": {k: v["status"] for k, v in state["steps"].items()},
                "manual_actions": state["manual_actions"],
            },
            indent=2,
        )
    )
    return (
        0
        if state["phase"] in ("COMPLETE", "COMPLETE_WITH_MANUAL_STEPS", "DRY_RUN_COMPLETE", "DRY_RUN_COMPLETE_WITH_MANUAL_STEPS")
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
