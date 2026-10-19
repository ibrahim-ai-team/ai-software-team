# GitHub Organization Workspace Architecture

## Purpose

Use the `ibrahim-ai-team` organization to host multiple software products while keeping the reusable AI delivery team separate from application code. This repository remains the shared, project-independent toolkit for agents, skills, standards, and delivery workflows.

## Repository boundaries

- **Platform/toolkit:** `ai-software-team` — reusable agents, skills, templates, standards, and orchestration workflows.
- **One repository per independently versioned deployable component:** for example, a backend API, frontend application, or worker service.
- **Testing repositories:** create a separate API, end-to-end, or performance test repository only when it has its own lifecycle, dependencies, access needs, or release cadence. Otherwise keep tests with the product they validate.
- **Infrastructure repositories:** create only when Docker/Kubernetes/CI infrastructure is shared or independently maintained. Keep product-specific deployment files with that product until reuse justifies extraction.
- **Shared services:** extract authentication, logging, or other common services only when there is a real consumer and a clear owner.

GitHub organizations do not provide nested repository folders. Use repository names, descriptions, topics, teams, and Projects to express the logical structure.

## Naming convention

Repositories are named after the app: the sponsor proposes the app name (or confirms one the Product Owner suggests), and its slug prefixes every repository, `<app>-<role>`. For "Shopinow":

- `shopinow-management`: coordination repository (requirements, ADRs, backlog epics, status); created when the project has more than one repository
- `shopinow-app`: the single application repository of a monolith
- `shopinow-front` / `shopinow-back`: separate frontend and backend
- `shopinow-<service>`: one repository per independently deployed service

Each idea also gets a hidden, stable project ID `idea-NN` (assigned by `scripts/provision_project.py`). It is used in topics, the description tag `[ai-team:idea-NN]`, issue labels and issue keys, so ideas never mix and renaming an app does not break tracking.

Create only the roles the approved architecture justifies. Every repository carries the topics `ai-team-app` and `idea-NN` and is linked to one GitHub Project board per idea. See `docs/project-provisioning.md`. This replaces the earlier `<product>-api` / `<product>-web` examples.

## Delivery workflow

1. Start each new product with discovery and explicit scope; do not scaffold every possible service up front.
2. Record architecture decisions and component boundaries before splitting repositories.
3. Deliver in small Agile sprints with prioritized stories, acceptance criteria, and a definition of done.
4. Work on feature branches and pull requests. Run relevant checks before merge.
5. Keep `main` protected where the GitHub plan and repository settings allow it; require review and passing checks when practical.
6. Use least-privilege GitHub Actions permissions and avoid committing credentials or environment secrets.
7. Keep a human responsible for approving and merging pull requests.

## Repository creation gate

Create a new repository only when all of these are known:

- the product or component has a clear purpose and named owner;
- its boundary and dependencies are understood;
- the initial backlog contains a meaningful first increment;
- the language/framework and test approach are selected;
- CI, secret handling, and contribution expectations are defined.

Do not create empty placeholder repositories just to imitate folders. Begin with the toolkit and one real product repository, then extract shared services or testing/infrastructure repositories when evidence supports the split.

## Suggested organization-wide governance

- Use consistent issue and pull-request templates across repositories.
- Use labels for type, priority, area, and sprint; keep label names consistent.
- Use GitHub Projects for cross-repository planning when multiple repositories actually exist.
- Keep reusable standards in this toolkit and link to them from product repositories.
- Review repository access, branch rules, Actions permissions, and secret protection independently for every repository.

## Current state

This document defines the intended structure; it does not mean any example repository has been created, configured, or protected. Verify each repository and setting in GitHub before treating governance controls as enforced.
