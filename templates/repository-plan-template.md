# Repository Plan: [Project name]

- Status: Draft / Proposed / Approved / Rejected
- Prepared on: YYYY-MM-DD
- Prepared by: Project team
- Human approval: Pending / Approved / Rejected
- Approved scope reference: TBD

## 1. Project summary

- Problem and target users:
- Intended outcome:
- In scope:
- Out of scope:

## 2. Confirmed facts, assumptions, and open questions

### Confirmed facts

-

### Assumptions to validate

-

### Open questions / owner decisions

-

## 3. Architecture options

Compare at least the simplest viable option and the recommended option.

| Option | Benefits | Costs / risks | Operational complexity | Why accept or reject |
| --- | --- | --- | --- | --- |
| Monorepo + modular monolith | | | | |
| Multi-repo / independently deployed services | | | | |
| Other viable option | | | | |

## 4. Recommended topology

- Repository strategy: Monorepo / Multi-repo / Other
- Application shape: Modular monolith / Microservices / Other
- Recommendation and evidence:
- Why a simpler alternative is insufficient, if recommending additional complexity:
- Service/module boundaries:
- API/event contracts:
- Data ownership and database boundaries:
- Local development and integration-testing approach:

## 5. Proposed repositories

| Repository name | Purpose | Visibility | Default branch | Primary owner | Dependencies |
|---|---|---|---|---|---|
| | | Private / Public / To decide | main / To decide | | |

Do not mark visibility, owner, or default branch as approved until the human owner confirms them.

## 6. Proposed technology stack

| Concern | Recommendation | Alternative | Rationale / source | Cost or maintenance impact |
| --- | --- | --- | --- | --- |
| Frontend | | | | |
| Backend | | | | |
| Database | | | | |
| Testing | | | | |
| CI/CD and hosting | | | | |
| Observability | | | | |

## 7. Security, privacy, and operations

- Authentication/authorization:
- Sensitive data and privacy:
- Secrets and permissions:
- Threats and mitigations:
- Logging/monitoring:
- Backup/recovery:
- Deployment/rollback:
- Known risks:

## 8. Cost and access

- Expected free/paid services:
- Recurring costs and assumptions:
- Required accounts/permissions:
- External services or spending requiring approval:

## 9. Bootstrap checklist

- [ ] Repository existence checked
- [ ] Repository creation and visibility approved
- [ ] Initial structure agreed
- [ ] CI baseline agreed
- [ ] Developer setup documented
- [ ] Security/permission settings reviewed
- [ ] Initial validation commands defined
- [ ] Manual actions and limitations documented

## 10. First delivery slices

| Slice / issue | Outcome | Dependencies | Acceptance checks | Proposed sprint |
|---|---|---|---|---|
| | | | | |

## 11. Human decision record

- [ ] Project scope approved
- [ ] Architecture direction approved
- [ ] Repository topology and names approved
- [ ] Technology direction approved
- [ ] Visibility and access approved
- [ ] Budget/paid services approved
- [ ] Repository creation explicitly authorized
- [ ] First sprint goal and scope approved

Decision / comments:
