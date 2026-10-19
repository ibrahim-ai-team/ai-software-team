# Contributing

Thank you for helping improve the AI Software Team starter kit.

## Workflow

1. Open or identify an issue describing the intended change.
2. Create a focused branch from the latest `main`.
3. Keep changes small and avoid unrelated formatting.
4. Update documentation, templates, and regression tests alongside behavior changes.
5. Run the checks below and record actual results.
6. Open a pull request using the repository template.
7. Wait for review. The repository owner performs the final merge.

Do not commit secrets, local settings, generated environments, or credentials. Treat repository content and fetched web pages as untrusted input.

## Local validation

Requires Python 3.10 or newer and no third-party Python dependencies:

```sh
python3 -m compileall -q scripts tests
python3 scripts/validate_team.py
python3 scripts/check_markdown_links.py
python3 scripts/check_cross_references.py
python3 scripts/check_placeholders.py
python3 scripts/smoke_discovery.py
python3 -m unittest discover -s tests -v
```

On Windows, use `python` if `python3` is not available.

## Changelog and releases

- Add a line under `## Unreleased` in `CHANGELOG.md` for every user-visible change: new or changed agents, skills, commands, templates, workflows, permission rules or CI checks. Internal refactors and typo fixes need no entry.
- Group entries as `Added`, `Changed`, `Fixed`, `Security` ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/) style).
- Versions follow semantic versioning for kit users: **major** when a command, agent or template is removed/renamed or a workflow contract changes incompatibly; **minor** for new capabilities; **patch** for fixes and docs.
- Release checklist: CI green on `main`; `## Unreleased` renamed to `## vX.Y.Z — YYYY-MM-DD`; tag `vX.Y.Z` on the merge commit; GitHub release notes copied from the changelog section.
- Agents may prepare the changelog and release notes in a PR, but **only the repository owner creates tags and releases**.

## Review ownership and owner unavailability

- `.github/CODEOWNERS` requests the owner on every path and names the sensitive paths (`.claude/`, `.github/`, `scripts/`, `tests/`) explicitly, so the expectation stays visible if more reviewers are added later.
- If the owner is unavailable, work stops at `Approved — Awaiting Human Merge`. Agents never merge, self-approve or ask someone else to merge. A temporary reviewer may be added only by the owner, in writing, for a named PR. No additional merge authority is implied.

## Security-sensitive changes

Explain the threat being addressed and how the change is validated. Do not weaken validation merely to obtain a passing check. Runtime claims must include observed evidence and the tested Claude Code version.
