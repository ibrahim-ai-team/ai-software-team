---
description: Turn an approved project plan into its GitHub workspace (repositories, issues, board) without duplicates
---

# Provision project

Run as `agile-orchestrator`, after discovery, architecture and backlog are done (`workflows/project-bootstrap.md` Gates 1–4). Full reference: `docs/project-provisioning.md`.

1. **Build the plan.** Write a plan file outside this repository's tracked files (for example `.provisioning/<idea>-plan.json`, which is git-ignored) using `templates/project-plan.example.json`:
   - App name: use the name the sponsor proposed (for example "Shopinow" gives the repositories shopinow-front and shopinow-back). If none was given, `product-owner` proposes one and the sponsor confirms it in the approval question. Set it as `project.name` (and `project.slug` if the repository prefix should differ).
   - `product-owner` and `business-analyst` supply the requirements and the backlog with acceptance criteria.
   - `software-architect` supplies `architecture.style` and the decision text (ADR). The style decides the repositories: "monolith" or "single-repo" gives one `<app>-app`; "frontend-backend" gives `<app>-front` and `<app>-back`; "services" gives one repository per service. A coordination repository `<app>-management` is added when there is more than one repository, unless the plan says otherwise.
   - `tech-lead` checks each repository's `stack`, `testing` and `setup`. `project-manager` sets the two-week sprint and priorities.
   - Never hard-code a stack in this repository; it belongs in the plan.
2. **Validate and show the tree.** Run `python3 scripts/provision_project.py plan <plan> --check-github`. It assigns the next free hidden project ID (`idea-NN`), rejects invalid plans and app names already used by another idea, and prints the repository tree and the plan digest. Fix every reported error before continuing.
3. **Ask the sponsor once.** Repository creation is a sponsor decision. Show the tree, visibility, the branch-protection option and the digest, and ask for approval. Record `approval.approved_by`, `approval.approved_at` and `approval.plan_digest` in the plan, and ask the sponsor to create `.claude/approvals/PROVISION-<project-id>.json` with `approved_by` and the same `plan_digest` (Claude cannot write it; see `.claude/approvals/README.md`). Any later change to the plan changes the digest, and `apply` will refuse until it is approved again.
4. **Dry run.** Run `python3 scripts/provision_project.py apply <plan> --dry-run`. This reads GitHub and writes nothing.
5. **Apply.** Run `python3 scripts/provision_project.py apply <plan>`. It creates or reuses each resource and records every step in `.provisioning/<idea>.json`. Scaffold files go to a branch named bootstrap/initial-structure with a PR in each repository. Nothing is written to `main`.
6. **Handle the result.**
   - `PERMISSION_DENIED` steps name the exact permission needed; report them to the sponsor.
   - `FAILED` and `SKIPPED_DEPENDENCY` steps: fix the cause and rerun the same command. Reruns are idempotent.
   - `BLOCKED` means an existing repository with that name was not created by this project. Choose another ID; never adopt it.
7. **Report.** Report the created resources, the manual actions and the bootstrap PRs awaiting the sponsor's merge. Then continue with `/plan-sprint` in the new project.

Never print tokens, never pass `--force` options, and never merge the bootstrap PRs.
