"""Unit tests for scripts/provision_project.py against an in-memory fake GitHub.

These are MOCKED tests: they prove planning, naming, idempotency and failure handling logic,
not the behaviour of the real GitHub API.
"""
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts import provision_project as pp

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = json.loads((ROOT / "templates" / "project-plan.example.json").read_text(encoding="utf-8"))


class FakeGitHub:
    def __init__(self):
        self.repos, self.projects, self.writes = {}, {}, []
        self.rules = []  # [op, match, exception, remaining] ; remaining None = always
        self.counter = 0

    def fail(self, op, exc, match="", times=None):
        self.rules.append([op, match, exc, times])

    def _check(self, op, target=""):
        for rule in self.rules:
            if rule[0] == op and rule[1] in target and (rule[3] is None or rule[3] > 0):
                if rule[3] is not None:
                    rule[3] -= 1
                raise rule[2]

    def _id(self, prefix):
        self.counter += 1
        return f"{prefix}{self.counter}"

    def _write(self, op, target=""):
        self._check(op, target)
        self.writes.append((op, target))

    # reads
    def list_org_repos(self, org):
        self._check("list_org_repos")
        return [{"name": n, "description": r["description"], "topics": r["topics"]} for n, r in self.repos.items()]

    def get_repo(self, org, name):
        self._check("get_repo", name)
        r = self.repos.get(name)
        return None if r is None else {"name": name, "description": r["description"],
                                       "default_branch": "main", "node_id": r["node_id"]}

    def get_topics(self, org, name):
        return list(self.repos[name]["topics"])

    def get_ref_sha(self, org, name, branch):
        return self.repos[name]["refs"].get(branch)

    def get_file(self, org, name, path, ref):
        return self.repos[name]["files"].get((ref, path))

    def find_pr(self, org, name, head):
        return next((p for p in self.repos[name]["prs"] if p["head"] == head), None)

    def list_labels(self, org, name):
        return set(self.repos[name]["labels"])

    def list_milestones(self, org, name):
        return dict(self.repos[name]["milestones"])

    def list_issues(self, org, name, label):
        self._check("list_issues", name)
        return [copy.deepcopy(i) for i in self.repos[name]["issues"] if label in i["labels"]]

    def find_project(self, org, title):
        p = self.projects.get(title)
        return None if p is None else copy.deepcopy(p)

    # writes
    def create_repo(self, org, name, description, visibility):
        self._write("create_repo", name)
        self.repos[name] = {"description": description, "visibility": visibility, "node_id": self._id("R_"),
                            "topics": [], "labels": set(), "milestones": {}, "issues": [],
                            "refs": {"main": "sha0"}, "files": {}, "prs": []}

    def set_topics(self, org, name, topics):
        self._write("set_topics", name)
        self.repos[name]["topics"] = list(topics)

    def create_ref(self, org, name, branch, sha):
        self._write("create_ref", name)
        self.repos[name]["refs"][branch] = sha

    def put_file(self, org, name, path, branch, text, message, sha=None):
        self._write("put_file", f"{name}/{path}")
        self.repos[name]["files"][(branch, path)] = (text, self._id("blob"))

    def create_pr(self, org, name, head, base, title, body):
        self._write("create_pr", name)
        pr = {"head": head, "html_url": f"https://github.com/{org}/{name}/pull/{len(self.repos[name]['prs']) + 1}"}
        self.repos[name]["prs"].append(pr)
        return pr

    def create_label(self, org, name, label, color):
        self._write("create_label", name)
        self.repos[name]["labels"].add(label)

    def create_milestone(self, org, name, title, due_on):
        self._write("create_milestone", name)
        number = len(self.repos[name]["milestones"]) + 1
        self.repos[name]["milestones"][title] = number
        return number

    def create_issue(self, org, name, title, body, labels, milestone):
        self._write("create_issue", name)
        issues = self.repos[name]["issues"]
        issue = {"number": len(issues) + 1, "title": title, "body": body, "labels": list(labels),
                 "milestone": milestone, "node_id": self._id("I_"),
                 "html_url": f"https://github.com/{org}/{name}/issues/{len(issues) + 1}"}
        issues.append(issue)
        return copy.deepcopy(issue)

    def update_issue_body(self, org, name, number, body):
        self._write("update_issue_body", name)
        self.repos[name]["issues"][number - 1]["body"] = body

    def protect_branch(self, org, name, branch):
        self._write("protect_branch", name)

    def create_project(self, org, title, description):
        self._write("create_project", title)
        self.projects[title] = {"id": self._id("P_"), "url": f"https://github.com/orgs/{org}/projects/1",
                                "description": description,
                                "repos": set(), "fields": {"Status", "Title"}, "items": set()}
        return copy.deepcopy(self.projects[title])

    def _project(self, project_id):
        return next(p for p in self.projects.values() if p["id"] == project_id)

    def link_project_repo(self, project_id, org, name):
        self._write("link_project_repo", name)
        self._project(project_id)["repos"].add(name)

    def add_project_item(self, project_id, content_id):
        self._write("add_project_item", content_id)
        self._project(project_id)["items"].add(content_id)

    def create_iteration_field(self, project_id, name, start, days):
        self._write("create_iteration_field", name)
        self._project(project_id)["fields"].add(name)


def plan(**overrides):
    raw = copy.deepcopy(EXAMPLE)
    raw.update(overrides)
    return raw


def run(fake, raw, dry_run=False, temp=None):
    normalized = pp.validate_plan(raw)
    path = Path(temp or tempfile.mkdtemp()) / f"{normalized['project']['id']}.json"
    client = pp.DryRunClient(fake) if dry_run else fake
    return pp.Provisioner(client, normalized, path, sleep=lambda s: None, dry_run=dry_run).run(), path


def statuses(state, prefix):
    return {k: v["status"] for k, v in state["steps"].items() if k.startswith(prefix)}


class NamingAndPlanTests(unittest.TestCase):
    def test_next_project_id(self):
        self.assertEqual(pp.next_project_id([]), "idea-01")
        self.assertEqual(pp.next_project_id(["ai-software-team", "shopinow-front", "idea-07-management"]), "idea-08")
        self.assertEqual(pp.next_project_id(["idea-99-back"]), "idea-100")
        tagged = [{"name": "shopinow-back", "description": "API [ai-team:idea-04]", "topics": []},
                  {"name": "booky-app", "description": "", "topics": ["ai-team-app", "idea-06"]}]
        self.assertEqual(pp.next_project_id(tagged), "idea-07")

    def test_repository_names_come_from_the_app_name(self):
        normalized = pp.validate_plan(plan(project={"id": "idea-01", "name": "Shopinow"}))
        self.assertEqual(normalized["project"]["slug"], "shopinow")
        self.assertEqual(pp.slugify("My Shop  2.0!"), "my-shop-2-0")
        custom = pp.validate_plan(plan(project={"id": "idea-01", "name": "Shop Now", "slug": "shopnow"}))
        self.assertEqual([r["name"] for r in custom["repos"]], ["shopnow-management", "shopnow-front", "shopnow-back"])

    def test_app_name_rules(self):
        for bad in ("ai-software-team", "idea-05", "Shop_Now", "-x"):
            with self.subTest(slug=bad), self.assertRaises(pp.PlanError) as ctx:
                pp.validate_plan(plan(project={"id": "idea-01", "name": "X", "slug": bad}))
            self.assertTrue(any("project.slug" in e for e in ctx.exception.errors))

    def test_app_name_used_by_another_idea_is_rejected(self):
        existing = [{"name": "shopinow-front", "description": "Store [ai-team:idea-03]", "topics": []}]
        with self.assertRaises(pp.PlanError) as ctx:
            pp.validate_plan(plan(project={"name": "Shopinow"}), existing_repos=existing)
        self.assertTrue(any("already used by idea-03" in e for e in ctx.exception.errors))
        same = pp.validate_plan(plan(project={"id": "idea-03", "name": "Shopinow"}), existing_repos=existing)
        self.assertEqual(same["project"]["id"], "idea-03")   # rerun of the same idea is fine

    def test_id_assigned_from_existing_repos_when_missing(self):
        raw = plan(project={"name": "Shopinow"})
        normalized = pp.validate_plan(raw, existing_repos=["ai-software-team", "idea-02-app"])
        self.assertEqual(normalized["project"]["id"], "idea-03")
        self.assertEqual([r["name"] for r in normalized["repos"]],
                         ["shopinow-management", "shopinow-front", "shopinow-back"])

    def test_frontend_backend_gets_management_front_back(self):
        roles = [r["role"] for r in pp.validate_plan(plan())["repos"]]
        self.assertEqual(roles, ["management", "front", "back"])

    def test_monolith_gets_one_repository_and_no_coordination_repo(self):
        raw = plan(architecture={"style": "monolith", "decision": "One deployable is enough."},
                   repositories=[{"role": "app", "purpose": "Shop", "stack": "Django", "testing": "pytest"}])
        for item in raw["backlog"]:
            item["repo"] = "app"
        normalized = pp.validate_plan(raw)
        self.assertEqual([r["name"] for r in normalized["repos"]], ["shopinow-app"])
        self.assertEqual(normalized["home_role"], "app")
        self.assertIn("docs/adr/0001-architecture.md", pp.scaffold_files(normalized, normalized["repos"][0]))

    def test_coordination_repo_can_be_forced_for_single_repo(self):
        raw = plan(architecture={"style": "single-repo", "decision": "CLI tool."}, coordination_repo=True,
                   repositories=[{"role": "app", "purpose": "CLI", "stack": "Go", "testing": "go test"}])
        for item in raw["backlog"]:
            item["repo"] = "management" if item["type"] == "epic" else "app"
        self.assertEqual([r["role"] for r in pp.validate_plan(raw)["repos"]], ["management", "app"])

    def test_services_style_uses_declared_services(self):
        raw = plan(architecture={"style": "services", "decision": "Independent scaling of search.",
                                 "has_frontend": True, "services": ["catalog", "orders"]})
        raw.pop("repositories")
        with self.assertRaises(pp.PlanError) as ctx:
            pp.validate_plan(raw)   # services need stack/testing before creation
        self.assertTrue(any("repositories[catalog].stack" in e for e in ctx.exception.errors))
        raw["repositories"] = [{"role": r, "purpose": r, "stack": "Go", "testing": "go test"}
                               for r in ("front", "catalog", "orders")]
        for item in raw["backlog"]:
            item["repo"] = {"back": "catalog"}.get(item["repo"], item["repo"])
        self.assertEqual([r["role"] for r in pp.validate_plan(raw)["repos"]],
                         ["management", "front", "catalog", "orders"])

    def test_invalid_plans_report_all_problems(self):
        raw = plan(project={"id": "shop", "name": ""})
        raw["repositories"][0]["stack"] = ""
        raw["backlog"][1]["repo"] = "mobile"
        raw["backlog"][2]["depends_on"] = ["US-9"]
        raw["backlog"][3]["acceptance_criteria"] = []
        with self.assertRaises(pp.PlanError) as ctx:
            pp.validate_plan(raw)
        text = " | ".join(ctx.exception.errors)
        for expected in ("project.id 'shop'", "project.name", "repositories[front].stack",
                         "repo 'mobile'", "depends_on 'US-9'", "QA-1: acceptance_criteria"):
            self.assertIn(expected, text)

    def test_dependency_cycle_is_rejected(self):
        raw = plan()
        raw["backlog"][1]["depends_on"] = ["US-2"]
        with self.assertRaises(pp.PlanError) as ctx:
            pp.validate_plan(raw)
        self.assertIn("dependency cycle", ctx.exception.errors[0])

    def test_organization_must_be_a_login(self):
        with self.assertRaises(pp.PlanError) as ctx:
            pp.validate_plan(plan(organization="ibrahim-ai-team/../x"))
        self.assertIn("organization must be a GitHub organization login", ctx.exception.errors)

    def test_reserved_role(self):
        raw = plan()
        raw["repositories"][0]["role"] = "management"
        with self.assertRaises(pp.PlanError):
            pp.validate_plan(raw)

    def test_tree_explains_grouping_and_lists_repositories(self):
        tree = pp.render_tree(pp.validate_plan(plan()))
        for text in ("cannot be nested", "ai-team-app", "shopinow-management", "shopinow-front", "shopinow-back",
                     "GitHub Project: \"Shopinow (idea-01)\""):
            self.assertIn(text, tree)


class ProvisioningTests(unittest.TestCase):
    def test_full_run_creates_linked_workspace(self):
        fake = FakeGitHub()
        state, path = run(fake, plan())
        self.assertEqual(state["phase"], "COMPLETE_WITH_MANUAL_STEPS")
        self.assertEqual(set(fake.repos), {"shopinow-management", "shopinow-front", "shopinow-back"})
        for repo in fake.repos.values():
            self.assertIn("[ai-team:idea-01]", repo["description"])
            self.assertEqual(repo["visibility"], "private")
            self.assertTrue({"ai-team-app", "idea-01"} <= set(repo["topics"]))
            self.assertEqual(len(repo["prs"]), 1)
            self.assertIn("Sprint 1", repo["milestones"])
            self.assertNotIn(("main", "README.md"), repo["files"])   # nothing is written to main
        issues = {i["title"]: i for r in fake.repos.values() for i in r["issues"]}
        self.assertEqual(len(issues), 4)
        us1 = issues["[US-1] Product catalogue API"]
        self.assertIn(us1["html_url"], issues["[US-2] Product list page"]["body"])   # cross-repo link
        self.assertIn("project:idea-01", us1["labels"])
        self.assertEqual(us1["milestone"], 1)
        project = fake.projects["Shopinow (idea-01)"]
        self.assertEqual(project["repos"], set(fake.repos))
        self.assertEqual(len(project["items"]), 4)
        self.assertIn("Sprint", project["fields"])
        report = fake.repos["shopinow-management"]["files"][(pp.BOOTSTRAP_BRANCH, "docs/provisioning-report.md")][0]
        self.assertIn("COMPLETE_WITH_MANUAL_STEPS", report)
        self.assertEqual(json.loads(path.read_text())["phase"], "COMPLETE_WITH_MANUAL_STEPS")
        self.assertFalse(any(op == "protect_branch" for op, _ in fake.writes))

    def test_rerun_is_idempotent(self):
        fake = FakeGitHub()
        run(fake, plan())
        before = copy.deepcopy((fake.repos, fake.projects))
        writes_before = len(fake.writes)
        state, _ = run(fake, plan())
        self.assertEqual(state["phase"], "COMPLETE_WITH_MANUAL_STEPS")
        self.assertEqual((fake.repos.keys(), len(fake.projects)), (before[0].keys(), len(before[1])))
        self.assertEqual(sum(len(r["issues"]) for r in fake.repos.values()), 4)
        self.assertEqual(sum(len(r["prs"]) for r in fake.repos.values()), 3)
        second = [op for op, _ in fake.writes[writes_before:]]
        self.assertEqual(second, ["put_file"], second)   # only the refreshed provisioning report
        self.assertFalse(set(statuses(state, "repo:").values()) - {"EXISTS"})

    def test_foreign_repository_blocks_without_changes(self):
        fake = FakeGitHub()
        fake.create_repo("ibrahim-ai-team", "shopinow-front", "someone else's repo", "public")
        fake.writes.clear()
        state, _ = run(fake, plan())
        self.assertEqual(state["phase"], "BLOCKED")
        self.assertIn("not created for idea-01", state["steps"]["preflight"]["detail"])
        self.assertEqual(fake.writes, [])

    def test_foreign_project_board_is_not_adopted(self):
        fake = FakeGitHub()
        fake.projects["Shopinow (idea-01)"] = {"id": "P_x", "url": "u", "description": "someone else's board",
                                                    "repos": set(), "fields": set(), "items": set()}
        state, _ = run(fake, plan())
        self.assertEqual(state["steps"]["project"]["status"], "FAILED")
        self.assertIn("not adopting it", state["steps"]["project"]["detail"])
        self.assertEqual(fake.projects["Shopinow (idea-01)"]["repos"], set())
        self.assertEqual(state["phase"], "PARTIAL")

    def test_tokens_are_redacted_from_recorded_errors(self):
        fake = FakeGitHub()
        fake.fail("create_label", pp.classify(500, "boom ghp_" + "a" * 36), times=5)
        state, path = run(fake, plan())
        self.assertNotIn("ghp_" + "a" * 36, path.read_text())
        self.assertIn("[redacted]", state["steps"]["labels:shopinow-management"]["detail"])

    def test_missing_project_permission_is_reported_not_faked(self):
        fake = FakeGitHub()
        fake.fail("create_project", pp.PermissionDenied(403, "Resource not accessible by integration"))
        state, _ = run(fake, plan())
        self.assertEqual(state["phase"], "PARTIAL")
        step = state["steps"]["project"]
        self.assertEqual(step["status"], "PERMISSION_DENIED")
        self.assertIn("organization Projects: read and write", step["detail"])
        self.assertEqual(fake.projects, {})
        self.assertEqual(sum(len(r["issues"]) for r in fake.repos.values()), 4)   # independent steps still ran

    def test_partial_failure_skips_dependents_and_resumes(self):
        fake = FakeGitHub()
        fake.fail("create_repo", pp.TransientError(502, "Bad gateway"), match="shopinow-back", times=3)
        state, _ = run(fake, plan())
        self.assertEqual(state["phase"], "PARTIAL")
        self.assertEqual(state["steps"]["repo:shopinow-back"]["status"], "FAILED")
        self.assertIn("after 2 retries", state["steps"]["repo:shopinow-back"]["detail"])
        self.assertEqual(state["steps"]["issue:US-1"]["status"], "SKIPPED_DEPENDENCY")
        self.assertEqual(state["steps"]["deps:US-2"]["status"], "SKIPPED_DEPENDENCY")
        self.assertIn("link pending for US-1", state["steps"]["deps:US-2"]["detail"])
        us2 = next(i for i in fake.repos["shopinow-front"]["issues"] if "US-2" in i["title"])
        self.assertIn("US-1 (link pending)", us2["body"])
        state, _ = run(fake, plan())   # transient failures exhausted: resume
        self.assertEqual(state["phase"], "COMPLETE_WITH_MANUAL_STEPS")
        self.assertEqual(sum(len(r["issues"]) for r in fake.repos.values()), 4)
        us2 = next(i for i in fake.repos["shopinow-front"]["issues"] if "US-2" in i["title"])
        self.assertIn("https://github.com/ibrahim-ai-team/shopinow-back/issues/1", us2["body"])

    def test_transient_error_is_retried(self):
        fake = FakeGitHub()
        fake.fail("create_label", pp.TransientError(503, "unavailable"), times=1)
        state, _ = run(fake, plan())
        self.assertEqual(state["steps"]["labels:shopinow-management"]["status"], "CREATED")

    def test_projects_never_share_issues_or_boards(self):
        fake = FakeGitHub()
        run(fake, plan())
        run(fake, plan(project={"id": "idea-02", "name": "Booky"}))
        self.assertEqual(set(fake.projects), {"Shopinow (idea-01)", "Booky (idea-02)"})
        owner = {"shopinow": "idea-01", "booky": "idea-02"}
        for name, repo in fake.repos.items():
            pid = owner[name.split("-")[0]]
            self.assertIn(f"[ai-team:{pid}]", repo["description"])
            for issue in repo["issues"]:
                self.assertEqual(issue["labels"][0], f"project:{pid}")
                self.assertIn(f"ai-team-key: {pid}/", issue["body"])
        self.assertEqual(fake.projects["Booky (idea-02)"]["repos"], {n for n in fake.repos if n.startswith("booky-")})

    def test_branch_protection_only_when_approved_in_plan(self):
        fake = FakeGitHub()
        raw = plan(options={"branch_protection": True, "project_board": False})
        state, _ = run(fake, raw)
        self.assertEqual(len([w for w in fake.writes if w[0] == "protect_branch"]), 3)
        self.assertNotIn("project", state["steps"])

    def test_dry_run_writes_nothing(self):
        fake = FakeGitHub()
        state, path = run(fake, plan(), dry_run=True)
        self.assertEqual(fake.writes, [])
        self.assertTrue(state["phase"].startswith("DRY_RUN_"))
        self.assertFalse(path.exists())
        self.assertEqual(statuses(state, "repo:"), {f"repo:shopinow-{r}": "DRY_RUN" for r in ("management", "front", "back")})


class GhClientErrorTests(unittest.TestCase):
    """GhClient with canned `gh` results (subprocess patched); no network."""

    def run_with(self, returncode=0, stdout="", stderr="", raises=None):
        from unittest import mock
        result = mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr)
        side = raises if raises else (lambda *a, **k: result)
        return mock.patch.object(pp.subprocess, "run", side_effect=side)

    def assert_raises(self, exc_type, **kw):
        with self.run_with(**kw), self.assertRaises(exc_type) as ctx:
            pp.GhClient()._api("GET", "repos/o/r")
        return ctx.exception

    def test_http_statuses(self):
        self.assertEqual(self.assert_raises(pp.PermissionDenied, returncode=1, stderr="gh: Forbidden (HTTP 403)").status, 403)
        self.assertIsInstance(self.assert_raises(pp.TransientError, returncode=1, stderr="gh: (HTTP 502)"), pp.TransientError)
        self.assertEqual(type(self.assert_raises(pp.GitHubError, returncode=1, stderr="gh: Not Found (HTTP 404)")), pp.GitHubError)

    def test_secondary_rate_limit_is_transient(self):
        exc = self.assert_raises(pp.TransientError, returncode=1,
                                 stderr="gh: You have exceeded a secondary rate limit (HTTP 403)")
        self.assertEqual(exc.status, 403)

    def test_graphql_errors_on_stdout_are_classified(self):
        body = json.dumps({"errors": [{"type": "INSUFFICIENT_SCOPES", "message": "needs project scope"}]})
        exc = self.assert_raises(pp.PermissionDenied, returncode=1, stdout=body, stderr="gh: needs project scope")
        self.assertIn("needs project scope", str(exc))

    def test_unknown_failure_is_not_retried_but_network_is(self):
        self.assertEqual(type(self.assert_raises(pp.GitHubError, returncode=1, stderr="gh: weird")), pp.GitHubError)
        self.assert_raises(pp.TransientError, returncode=1, stderr="error connecting to api.github.com")

    def test_missing_gh_binary(self):
        exc = self.assert_raises(pp.GitHubError, raises=FileNotFoundError("gh"))
        self.assertIn("gh CLI is not installed", str(exc))

    def test_get_repo_returns_none_on_404(self):
        with self.run_with(returncode=1, stderr="gh: Not Found (HTTP 404)"):
            self.assertIsNone(pp.GhClient().get_repo("o", "r"))


class RobustnessTests(unittest.TestCase):
    def test_repo_failure_skips_project_instead_of_crashing(self):
        fake = FakeGitHub()
        fake.fail("create_repo", pp.PermissionDenied(403, "no"), match="shopinow-front")
        state, path = run(fake, plan())
        self.assertEqual(state["steps"]["repo:shopinow-front"]["status"], "PERMISSION_DENIED")
        self.assertEqual(state["steps"]["project"]["status"], "SKIPPED_DEPENDENCY")
        self.assertEqual(json.loads(path.read_text())["phase"], "PARTIAL")

    def test_unexpected_exception_is_recorded(self):
        fake = FakeGitHub()
        fake.fail("create_label", KeyError("boom"), match="shopinow-back")
        state, _ = run(fake, plan())
        self.assertIn("unexpected KeyError", state["steps"]["labels:shopinow-back"]["detail"])
        self.assertEqual(state["phase"], "PARTIAL")

    def test_concurrently_created_label_counts_as_existing(self):
        fake = FakeGitHub()
        fake.fail("create_label", pp.GitHubError(422, "Validation Failed: already_exists"), times=1)
        state, _ = run(fake, plan())
        self.assertEqual(state["steps"]["labels:shopinow-management"]["status"], "CREATED")

    def test_report_not_written_to_closed_bootstrap_branch(self):
        fake = FakeGitHub()
        run(fake, plan())
        fake.repos["shopinow-management"]["prs"][0]["state"] = "closed"
        writes = len(fake.writes)
        state, _ = run(fake, plan())
        self.assertNotIn(("put_file", "shopinow-management/docs/provisioning-report.md"), fake.writes[writes:])
        self.assertIn("bootstrap PR closed", state["steps"]["report"]["detail"])


class ApprovalGateTests(unittest.TestCase):
    def write_plan(self, raw, folder):
        path = Path(folder) / "plan.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        return str(path)

    def main(self, *args, client):
        out = io.StringIO()
        with redirect_stdout(out):
            code = pp.main(list(args), client=client)
        return code, out.getvalue()

    def test_apply_requires_matching_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = FakeGitHub()
            code, out = self.main("apply", self.write_plan(plan(), folder), "--state-dir", folder, client=fake)
            self.assertEqual(code, 4)
            self.assertIn("Refusing to provision", out)
            self.assertEqual(fake.writes, [])
            digest = pp.plan_digest(pp.validate_plan(plan()))
            approved = plan(approval={"approved_by": "IbrhimGhorafi", "approved_at": "2026-10-20", "plan_digest": digest})
            code, out = self.main("apply", self.write_plan(approved, folder), "--state-dir", folder, client=fake)
            self.assertEqual(code, 0, out)
            self.assertEqual(len(fake.repos), 3)

    def test_changed_plan_invalidates_approval(self):
        digest = pp.plan_digest(pp.validate_plan(plan()))
        changed = plan(visibility="public", approval={"approved_by": "x", "plan_digest": digest})
        with tempfile.TemporaryDirectory() as folder:
            fake = FakeGitHub()
            code, _ = self.main("apply", self.write_plan(changed, folder), "--state-dir", folder, client=fake)
            self.assertEqual(code, 4)
            self.assertEqual(fake.repos, {})

    def test_plan_command_prints_tree_and_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            code, out = self.main("plan", self.write_plan(plan(), folder), client=FakeGitHub())
        self.assertEqual(code, 0)
        self.assertIn("shopinow-management", out)
        self.assertIn("Plan digest:", out)

    def test_plan_permission_failure_names_permission(self):
        fake = FakeGitHub()
        fake.fail("list_org_repos", pp.PermissionDenied(403, "forbidden"))
        with tempfile.TemporaryDirectory() as folder:
            code, out = self.main("plan", self.write_plan(plan(project={"name": "X"}), folder), "--check-github", client=fake)
        self.assertEqual(code, 3)
        self.assertIn("read access to the organization's repositories", out)


if __name__ == "__main__":
    unittest.main()
