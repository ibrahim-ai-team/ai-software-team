# Project Bootstrap Workflow

## Purpose and scope

Use this workflow when the user provides a software idea and asks the team to build it. The team—not the user—owns discovery, specification, backlog preparation, architecture analysis, task decomposition, and routine delivery planning. The user is the project sponsor/supervisor: they follow progress and retain final PR merge authority. This workflow applies to future application projects, not changes to this reusable AI team starter kit.

## Phase Discovery — brief PO, spec BA, validation PO, approbation CP1

Avant la création du backlog ou la planification de l'implémentation, respecter cet ordre strict :

1. **Product Owner — brief de valeur métier :** documente why, for whom/persona, success metrics, priorité P0/P1/P2 et scope haut niveau (in/out).
2. **Business Analyst — spec EARS :** rédige seul la spécification finale à partir du brief PO : EARS formel, contraintes non fonctionnelles applicables, workflows et edge cases, Gherkin, matrice requirement → test, glossaire, hypothèses et questions ouvertes.
3. **Product Owner — validation métier :** vérifie la cohérence de la spec avec le brief et retourne des commentaires précis au BA. Le PO ne réécrit pas la spec.
4. **Humain — CP1 :** approuve le plan/la spec. Une validation agent ne remplace jamais l'approbation humaine.

Si le PO et le BA divergent, l'orchestrateur arbitre le processus et escalade toute décision de valeur/priorité/scope au PO ou au sponsor selon l'autorité définie. Une story sans spec EARS validée et approbation CP1 enregistrée ne passe pas G1 ; voir `standards/spec-driven-development.md` et `standards/validation-gates.md`.

## Étape 1 — créer les worktrees par agent

Before delegating any task that writes repository files, the orchestrator runs `./scripts/new_worktree.sh <agent> <story>` and passes the resulting path, branch, and allowed paths to that agent. Each writing agent works only in its assigned worktree; concurrent writing tasks never share a worktree. At story completion, preserve/commit the work and run `./scripts/cleanup_worktree.sh <agent> <story>`; cleanup requires confirmation. Never write directly to `main`. See `standards/agent-isolation.md`.

## Workflow gates

- **Phase Discovery — Spec EARS avant backlog :** suivre l'ordre PO brief → BA spec → PO validation → approbation humaine CP1. Le BA est l'unique auteur de la spec EARS ; le PO décide priorité/scope et valide la cohérence métier sans réécrire la spec. Toute divergence remonte à l'orchestrateur. Une story sans spec validée et approbation CP1 enregistrée ne passe pas G1 ; voir `standards/spec-driven-development.md`.

- **Gate 1 — Worktree isolation:** create a dedicated worktree for each writing agent/story with `scripts/new_worktree.sh`; no shared worktree for concurrent writers. Clean up with the confirmation-protected cleanup script after the story.
- **Gate 0 — Activation:** A clear request such as "build an e-commerce site" activates the workflow; do not demand that the user write a complete project brief.
- **Gate 1 — Discovery and specification:** Product Owner and Business Analyst derive the product brief, user personas/journeys, functional and non-functional requirements, scope boundaries, assumptions, risks, acceptance criteria, and unresolved questions. Ask the user only for material decisions that cannot safely be inferred. Record assumptions explicitly.
- **Gate 2 — Architecture options:** Software Architect compares reasonable stack and system-shape options, including monorepo/multi-repo and modular monolith/microservices where relevant. Recommend the simplest architecture that meets the requirements; include trade-offs, operational burden, security, cost, and alternatives. Do not assume microservices or a framework by default.
- **Gate 3 — Backlog and delivery plan:** Project Manager converts the specification into prioritized epics/stories/tasks, dependencies, estimates, verification criteria, and proposed sprint slices. QA creates an initial test strategy; DevOps plans the development workflow and CI/CD. The Project Manager owns routine planning and sequencing so the user does not need to manage tasks.
- **Gate 4 — Sponsor decision checkpoint:** Present a concise baseline plan and highlight only decisions that materially affect product direction, costs, security/privacy, access, external commitments, or irreversible choices. Routine product/technical choices may proceed as documented recommendations and assumptions. Do not treat silence as authorization for paid services, production deployment, destructive actions, permission changes, or external repository creation where target/visibility/access are unclear.
- **Gate 5 — Project setup:** Run `/provision-project`. The orchestrator builds the project plan from the Gate 1–4 outputs, validates it and shows the repository tree, obtains the sponsor's approval of the plan digest, then provisions repositories named `<app>-<role>` after the sponsor's app name, bootstrap PRs, labels, milestones, issues and the Project board idempotently with `scripts/provision_project.py`. Missing permissions are reported with the exact permission needed; nothing is claimed as created without the step record. See `docs/project-provisioning.md`.
- **Gate 6 — Bootstrap verification:** Verify repository structure, setup instructions, CI baseline, test commands, and available permissions. Report actual checks and limitations.
- **Gate 7 — Begin delivery:** Project Manager initializes backlog/sprint records and starts bounded, Ready tasks. Do not ask the user to approve every task or routine sprint item. Follow workflows/agile-agent-delivery.md; use isolated branches/worktrees and PRs. The human owner performs every final merge.

## Role ownership

- **Agile Orchestrator (`agile-orchestrator`):** single entry point; delegates every phase, verifies results, owns GitHub writes and reports to the sponsor.
- **Tech Lead (`tech-lead`):** validates the stack for buildability, splits stories into small tasks, sets implementation standards and reviews PRs for technical quality.

- **Product Owner :** décide de la valeur métier, des personas, des métriques de succès, de la priorité et du scope haut niveau ; valide la spec métier sans la réécrire.
- **Business Analyst :** seul auteur de la spec EARS finale, des workflows/edge cases, critères Gherkin, glossaire, hypothèses et matrice de traçabilité.
- **Software Architect:** evaluate architecture and repository options, define boundaries/API contracts, record ADRs, and advise on technical quality. Technical review belongs to `tech-lead`; `code-review-security` performs the independent read-only security review; the orchestrator records review disposition.
- **Project Manager / Scrum Master:** sequence work, manage dependencies and work in progress, prepare delegation records for the orchestrator to dispatch, update task state, and publish daily reports.
- **DevOps / Repository Setup:** scaffold the approved environment, CI, developer setup, and operational baseline; do not create unapproved external resources or incur costs.
- **Backend / Frontend / Database agents:** implement bounded slices after requirements and acceptance criteria are ready.
- **QA Automation:** prepare risk-based test strategy early and verify changes with actual evidence.
- **Code Review / Security:** assess designs and diffs against quality and security requirements.
- **User / sponsor:** supplies the idea and essential business constraints, monitors progress, answers escalated material decisions, and performs final PR merges.

## Architecture decision checklist

Evaluate functional and non-functional requirements, release/deployment boundaries, shared code/versioning, local development and integration-test complexity, CI/CD maintenance, permissions/secrets/privacy, operating costs/observability/resilience, scale, and operational maturity.

Default to the simplest architecture that meets confirmed requirements. Microservices require concrete justification and documented service boundaries, communication, data ownership, observability, failure handling, local development, and testing.

## Required bootstrap deliverables

1. Product brief and requirements summary.
2. Confirmed facts, assumptions, open questions, and out-of-scope items.
3. User journeys, user stories, acceptance criteria, and requirements-to-test traceability.
4. Architecture/stack comparison with recommendation and trade-offs.
5. Repository/environment plan using templates/repository-plan-template.md where applicable.
6. Security/privacy risks, operational needs, cost assumptions, and dependencies.
7. Prioritized backlog and proposed first delivery slices.
8. Initial QA strategy and CI/CD plan.
9. Concise sponsor checkpoint listing only decisions that genuinely need human input.

## Repository setup execution checklist

When target and permissions are available:

1. Reconfirm target owner/organization and intended visibility.
2. Check whether each repository already exists to avoid duplicates.
3. Create only resources within explicit authorization and permissions.
4. Use the agreed default branch and baseline files.
5. Add only approved collaborators, permissions, integrations, and secret references; never print or commit secret values.
6. Add baseline CI/static checks and setup documentation appropriate to the selected stack.
7. Keep implementation work on feature branches and open PRs for code/configuration changes where supported.
8. Record exact repository URLs, initial commit/branch, setup steps, checks run, limitations, and manual actions needed.
9. Stop if permissions, visibility, costs, or an irreversible choice differs from authorization.

## Pause and escalation rules

Pause and ask the sponsor only when requirements materially conflict, an important product decision cannot be inferred, an architecture choice changes cost/risk significantly, a repository/resource is unexpectedly present, credentials/permissions are missing, or the next action exceeds authorized scope. Explain evidence, impact, options, recommendation, and exact decision needed.

## Completion definition

Bootstrap is complete when the specification and assumptions are documented, architecture and repository decisions are recorded, a prioritized backlog and verification plan exist, setup is verified to the extent available, and the Project Manager has established durable tracking and the first delivery plan. It does not mean the application itself is implemented.
