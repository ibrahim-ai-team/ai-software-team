# GitHub Actions hardening standard

## Required controls

- Set workflow-level `permissions` explicitly. Default to `contents: read`; add a write permission only for a job that demonstrably needs it.
- Prefer job-level permissions when jobs have different needs. Do not use `write-all` or broad write scopes.
- Keep `pull_request` workflows read-only. Do not expose write-capable secrets to untrusted fork code.
- For workflows that mutate GitHub Projects or other resources, use a separately scoped secret only when required; document its owner, minimum scopes, rotation and exposure boundaries. `GITHUB_TOKEN` permissions do not limit a separate PAT secret.
- Pin third-party Actions to full commit SHAs and add a version comment. Use Dependabot to keep pinned versions updated.
- Set `persist-credentials: false` on checkout unless authenticated Git operations are required.
- Use explicit timeouts, concurrency controls where appropriate, and input validation for dispatchable workflows.
- Avoid interpolating untrusted event text directly into shell scripts. Pass values through environment variables and validate them.
- Keep secrets out of logs and artifacts. Do not echo tokens or enable shell tracing around secrets.
- Prefer read-only checks and local/stdlib validation over privileged scripts or unnecessary dependencies.

## Workflow review checklist

For every change under `.github/workflows/`, reviewers verify:

- [ ] Trigger is limited to the events required by the workflow.
- [ ] Workflow and job permissions are explicit and minimal; no `write-all`.
- [ ] Each write permission has a documented need; PR jobs remain read-only.
- [ ] Every third-party Action is pinned to a full commit SHA.
- [ ] Checkout uses `persist-credentials: false` unless justified.
- [ ] Secrets are scoped, passed through environment variables, and never printed.
- [ ] Untrusted inputs are validated and not injected into shell source.
- [ ] Concurrency, timeout, and failure behavior are appropriate.
- [ ] The workflow is covered by static validation/tests where practical.
- [ ] Changes and any exceptions are documented in the PR.

## Current workflow audit

The existing `.github/workflows/pre-commit.yml`, `project-status.yml`, `secret-scan.yml`, and `validate-team.yml` were audited for this change. Each currently declares `permissions: contents: read`; none uses `write-all`. The Project status workflow uses the separately configured `PROJECTS_TOKEN` secret for GraphQL mutations, so that token's scopes must be restricted independently of the workflow's `GITHUB_TOKEN` permissions. Re-audit whenever a workflow or required API operation changes.
