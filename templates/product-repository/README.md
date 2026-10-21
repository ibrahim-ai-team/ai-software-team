# Product Repository Bootstrap Template

Use this checklist when a real application is approved. Do not create placeholder repositories solely to represent folders in the organization.

## Repository metadata

- **Name:** `<app>-<role>` after the sponsor's app name (for example `shopinow-back`), created by `scripts/provision_project.py`
- **Description:** One sentence stating component purpose and owner
- **Topics:** Product name plus relevant areas such as `backend`, `frontend`, `testing`, or `infrastructure`
- **Visibility:** Choose deliberately based on product confidentiality
- **License:** Decide before publishing as open source

## Minimum starting layout

Adapt this structure to the chosen language and framework; do not add empty folders that the product does not need.

```text
<product-component>/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
├── docs/
│   ├── architecture/
│   └── decisions/
├── src/
├── tests/
├── .gitignore
├── README.md
├── CONTRIBUTING.md
└── SECURITY.md
```

For frontend/backend repositories, use the conventions of the selected framework. For a test-only repository, replace `src/` with a suitable test directory such as `tests/api/` or `tests/e2e/`.

## Required first increment

Before implementation begins, record:

- Problem statement and target users
- In-scope and out-of-scope requirements
- Acceptance criteria for the first user story
- Architecture and framework decision
- Test strategy and Definition of Done
- CI checks, secret handling, and owner for deployment
- Initial backlog ordered into small sprint-sized increments

## Pull request checklist

- [ ] Change is limited to the stated story
- [ ] Tests added or updated and relevant checks pass
- [ ] No credentials or sensitive data committed
- [ ] Documentation and configuration updated
- [ ] Risks and rollback considerations documented where relevant
- [ ] Human reviewer approves before merge

## Shared toolkit

Use the reusable standards and workflows from [ai-software-team](https://github.com/ibrahim-ai-team/ai-software-team). Copy or adapt only the relevant parts into the product repository; keep product-specific decisions with the product.
