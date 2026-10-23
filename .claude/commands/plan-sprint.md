---
description: Prepare a bounded sprint plan from a verified backlog
---

# Plan sprint

Rules: `workflows/sprint-governance.md` (planning, scope protection, next sprint) and `standards/sprint-sizing.md` (points and capacity). This command only sequences the work; it does not restate those rules.

1. Read the project state (goal, MVP scope, release criteria, open requirement conflicts), the previous sprint record and its review, and the open backlog with its Project priority fields. Do not plan while a conflict affecting the goal is open; ask the decision owner first.
2. Ask `product-owner` for priority and the sprint goal, `tech-lead` for points and task breakdown, and `project-manager` (Scrum Master) for capacity, dependencies and risk. Skills: `agile-planning`, `token-context-cost-management`. Plan once per sprint; reuse the plan unless new information changes it.
3. Select Ready issues (`workflows/backlog-quality-gates.md`) in priority order until capacity is reached. Previous-sprint candidates compete with the rest of the backlog; nothing carries over automatically. Include QA, security, documentation and delivery work.
4. Write the sprint record from `templates/sprint-plan-template.md` with the next Sprint ID, real dates, committed issues and out-of-scope items, then run `python scripts/check_governance.py <sprint records>`.
5. Record the approval in `Approved by`: the sponsor's decision, or the `product-owner` under a recorded standing delegation when the plan stays within the approved MVP scope, capacity and release criteria (`workflows/sprint-governance.md#sprint-planning`). Report the goal, committed issues, capacity, risks and out-of-scope items to the sponsor either way. Do not start the sprint, or claim membership on GitHub (milestone or Project field), without that approval and a read-back of the GitHub change.
