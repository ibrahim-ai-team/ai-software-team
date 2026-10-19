# Organization Setup Blueprint — ibrahim-ai-team

## Goal

Prepare the GitHub organization for incremental AI-assisted software delivery while keeping the reusable AI team separate from application repositories. This blueprint is documentation and a checklist; it does not itself change organization settings or create application repositories.

## 1. Logical organization layout

GitHub organizations do not have nested repository folders. Represent the layout with consistent repository names, descriptions, topics, pinned repositories, and GitHub Projects.

| Logical area | Repository naming pattern | When to create |
|---|---|---|
| Shared AI delivery platform | `ai-software-team` | Exists; reusable agents, skills, standards, templates, workflows. Never copied per application |
| Project coordination | `<app>-management` (e.g. `shopinow-management`) | When an idea's architecture has more than one repository |
| Single-repository application | `<app>-app` | Monolith or single-repo architecture |
| Frontend / backend | `<app>-front`, `<app>-back` | Frontend-backend architecture |
| Independent service | `<app>-<service>` | Only for services with their own deployment |
| Organization profile and shared community health files | `.github` | Create a special repository named exactly `.github` when ready |

Do not create empty application repositories just to imitate folders. Start new repositories when a real product and its first increment are understood.

## 2. Suggested organization profile

**Short description**
> An AI-assisted software engineering workspace for building software incrementally with reusable agents, skills, quality gates, and Agile workflows.

**Profile README draft**

> # Ibrahim AI Team
>
> Building software with a coordinated AI-assisted engineering workflow.
>
> We maintain reusable agents, skills, engineering standards, and delivery workflows, then apply them to real products through small, reviewable increments.
>
> ## Focus
> - Business analysis and product planning
> - Backend and frontend engineering
> - QA automation and test strategy
> - DevOps, CI/CD, and infrastructure
> - Security, code review, and release readiness
>
> ## Start here
> - [AI Software Team toolkit](https://github.com/ibrahim-ai-team/ai-software-team)
>
> ## Engineering principles
> - Deliver in small Agile increments
> - Automate checks and test continuously
> - Keep credentials out of source control
> - Use pull requests and human approval before merging
> - Document decisions and verify claims with evidence
>
> This organization is evolving; repositories and controls are documented as implemented, not assumed.

This profile text is a proposal, not yet published on the organization profile.

## 3. Suggested topics

Use a small, consistent set of GitHub topics where applicable:
- `ai-agents`
- `software-engineering`
- `agile`
- `qa-automation`
- `devops`
- `security`

Apply only topics that accurately describe each repository.

## 4. Repository descriptions

- `ai-software-team`: "Reusable AI-assisted software delivery toolkit: agents, skills, engineering standards, templates, and Agile workflows."
- Future product repositories: describe the component, primary technology where known, and purpose in one sentence.
- Avoid describing planned repositories as if they already exist.

## 5. Organization setup checklist

### Profile and discoverability
- [ ] Review organization display name, description, website, location, and avatar.
- [ ] Create the special `.github` repository and publish a profile README.
- [ ] Pin `ai-software-team` after reviewing its README and license.
- [ ] Add concise descriptions and relevant topics to repositories.

### Governance and security
- [ ] Review organization member roles and app installation access.
- [ ] Review Actions permissions and third-party action pinning.
- [ ] Enable GitHub Secret Scanning and Push Protection if available for the plan and repository visibility.
- [ ] Verify the free Gitleaks CLI workflow has a successful run.
- [ ] Review rulesets/branch protection on `main`; require checks and review where supported.
- [ ] Confirm the human owner approves merges.
- [x] Choose and document a repository license before representing the toolkit as open source (MIT, #36).

### Planning and delivery
- [ ] Create a GitHub Project only when there is a real product backlog to manage.
- [ ] Standardize issue labels and pull request templates.
- [ ] Create a new application repository only after product scope, owner, initial backlog, stack, test approach, and CI expectations are defined.

## 6. Implementation boundary

The organization profile and special `.github` repository are separate from `ai-software-team`. This document prepares the content and checklist, but publishing the organization profile, changing organization-level settings, and creating other repositories are separate GitHub operations. Verify each operation after it is performed.
