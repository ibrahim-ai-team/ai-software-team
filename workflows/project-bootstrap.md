# Project Bootstrap Workflow

## Purpose and scope

Use this workflow when the user provides a software idea and asks the team to build it. The team, not the user, owns discovery, specification, backlog preparation, architecture analysis, task decomposition and routine delivery planning. The user is the sponsor/supervisor: they follow progress, answer escalated material decisions and keep final PR merge authority. This workflow applies to future application projects, not to changes to this reusable AI team kit. Role ownership and decision authority are in `standards/agent-contract.md`.

## Discovery phase — PO brief, BA specification, PO validation, CP1 approval

Before creating the backlog or planning implementation, follow this strict order:

1. **Product Owner — business-value brief:** why, target user/persona, success metrics, P0/P1/P2 priority and high-level in/out scope.
2. **Business Analyst — EARS specification:** solely author the final specification from the PO brief: formal EARS, applicable non-functional constraints, workflows and edge cases, Gherkin, requirement-to-test traceability, glossary, assumptions and open questions.
3. **Product Owner — business validation:** check the specification against the brief and return precise comments to the BA. The PO does not rewrite the specification.
4. **Human — CP1:** approve the plan/specification. Agent validation never replaces human approval.

If the PO and BA disagree, the orchestrator routes business-value, priority or scope decisions to the PO or sponsor under the authority rules. A story without a validated EARS specification and recorded CP1 approval cannot pass G1 (`standards/spec-driven-development.md`, `standards/validation-gates.md`).

## Worktree isolation

Before delegating any task that writes repository files, the orchestrator runs `./scripts/new_worktree.sh <agent> <story>` and gives the agent the resulting path, branch and allowed paths. Concurrent writers never share a worktree. At story completion, preserve and commit the work, then run `./scripts/cleanup_worktree.sh <agent> <story>` (cleanup requires confirmation). Never write directly to `main`. See `standards/agent-isolation.md`.

## Workflow gates

- **Gate 0 — Activation:** a clear request such as "build an e-commerce site" activates the workflow; never demand that the user write a complete brief first.
- **Gate 1 — Discovery and specification:** follow the discovery phase above. PO and BA derive the brief, personas and journeys, functional and non-functional requirements, scope boundaries, assumptions, risks, acceptance criteria and open questions. Ask the user only for material decisions that cannot safely be inferred.
- **Gate 2 — Architecture options:** the Architect compares reasonable stack and system-shape options, including monorepo/multi-repo and modular monolith/microservices where relevant, and recommends the simplest architecture that meets the requirements, with trade-offs, operational burden, security, cost and alternatives.
- **Gate 3 — Backlog and delivery plan:** the PM turns the specification into prioritized epics, stories and tasks with dependencies, estimates, verification criteria and sprint slices; QA writes an initial test strategy; DevOps plans the development workflow and CI/CD.
- **Gate 4 — Sponsor decision checkpoint:** present a concise baseline plan and raise only decisions that materially affect product direction, cost, security/privacy, access, external commitments or irreversible choices. Routine choices proceed as documented recommendations. Silence never authorizes paid services, production deployment, destructive actions, permission changes, or external repository creation where target, visibility or access is unclear.
- **Gate 5 — Project setup:** run `/provision-project`. The orchestrator builds the project plan from Gates 1–4, validates it and shows the repository tree, obtains the sponsor's approval of the plan digest, then provisions repositories named `<app>-<role>`, bootstrap PRs, labels, milestones, issues and the Project board idempotently with `scripts/provision_project.py`. Missing permissions are reported with the exact permission needed; nothing is claimed as created without its step record. See `docs/project-provisioning.md`.
- **Gate 6 — Bootstrap verification:** verify repository structure, setup instructions, CI baseline, test commands and available permissions; report actual checks and limitations.
- **Gate 7 — Begin delivery:** the PM initializes backlog and sprint records and starts bounded Ready tasks under `workflows/agile-agent-delivery.md`, on isolated branches/worktrees with PRs. Do not ask the user to approve every task. The human owner performs every final merge.

## Architecture decision checklist

Evaluate functional and non-functional requirements, release and deployment boundaries, shared code and versioning, local development and integration-test complexity, CI/CD maintenance, permissions, secrets and privacy, operating cost, observability, resilience, scale and operational maturity.

Default to the simplest architecture that meets confirmed requirements. Microservices require concrete justification and documented service boundaries, communication, data ownership, observability, failure handling, local development and testing.

## Required bootstrap deliverables

1. Product brief and requirements summary.
2. Confirmed facts, assumptions, open questions and out-of-scope items.
3. User journeys, user stories, acceptance criteria and requirements-to-test traceability.
4. Architecture/stack comparison with recommendation and trade-offs.
5. Repository/environment plan using `templates/repository-plan-template.md` where applicable.
6. Security/privacy risks, operational needs, cost assumptions and dependencies.
7. Prioritized backlog and proposed first delivery slices.
8. Initial QA strategy and CI/CD plan.
9. A concise sponsor checkpoint listing only decisions that genuinely need human input.

## Repository setup execution checklist

When target and permissions are available:

1. Reconfirm the target owner/organization and intended visibility.
2. Check whether each repository already exists, to avoid duplicates.
3. Create only resources within explicit authorization and permissions.
4. Use the agreed default branch and baseline files.
5. Add only approved collaborators, permissions, integrations and secret references; never print or commit secret values.
6. Add baseline CI/static checks and setup documentation for the selected stack.
7. Keep implementation on feature branches with PRs where supported.
8. Record repository URLs, initial commit/branch, setup steps, checks run, limitations and manual actions needed.
9. Stop if permissions, visibility, costs or an irreversible choice differ from the authorization.

## Pause and escalation rules

Pause and ask the sponsor only when requirements materially conflict, an important product decision cannot be inferred, an architecture choice changes cost or risk significantly, a repository or resource unexpectedly exists, credentials or permissions are missing, or the next action exceeds authorized scope. Give the evidence, impact, options, recommendation and the exact decision needed.

## Completion definition

Bootstrap is complete when the specification and assumptions are documented, architecture and repository decisions are recorded, a prioritized backlog and verification plan exist, setup is verified as far as available, and the PM has established durable tracking and the first delivery plan. It does not mean the application is implemented.
