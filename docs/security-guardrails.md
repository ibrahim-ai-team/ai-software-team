# Security Guardrails: Threat Model, Limits and Verification

Scope: the permission rules in `.claude/settings.json`. These are **client-side, best-effort controls**, not a sandbox. Static validation and tests prove only that rules are present and well-formed; they do **not** prove Claude Code enforces them.

## Threat model

| Threat | Intended control | Enforcement status |
| --- | --- | --- |
| Force-push or push to `main` using alternate refspecs or flags | Deny selected push patterns; ask before other pushes | Client-side only; runtime not verified. GitHub rulesets are required for server-side protection. |
| Destructive recursive deletion | Deny selected recursive-delete patterns; ask for `rm -r`/`-R` | Client-side only; runtime not verified. |
| Secret disclosure through common shell commands | Deny selected commands and `.env` path patterns | Best effort; other tools and interpreters can bypass string patterns. |
| Reading or editing secret files through file tools | Deny Read/Edit for `.env`, key/certificate files and `secrets/**` | Client-side only; does not constrain shell access. |
| Editing or writing permission settings, shared Claude instructions/manifest, CI workflows, CODEOWNERS or Dependabot configuration | Ask for confirmation for both `Edit` and `Write` tools | Confirmation only; not a sandbox. |
| Repository settings/API actions | Ask for confirmation on selected `gh` commands | Depends on confirmation and token scope. |
| Missing branch protection | Owner checklist below | Documentation only; repository settings have not been verified. |

The intended permission precedence is deny, then ask, then default behavior. Confirm the exact semantics against the installed Claude Code version.

## Known limits

- Other interpreters such as Python, Perl, Node.js or Ruby may read secrets without matching the shell rules.
- Wrappers such as `bash -c`, `sh -c`, `env`, `xargs`, aliases and absolute executable paths may evade prefix patterns.
- Shell writes such as `echo >`, `tee` or `sed -i` are not covered by file-tool `Edit` rules.
- An agent with arbitrary shell execution may be able to modify the settings file through another route.
- `.env*` rules can also block example files; broad `printenv` blocking can create false positives.
- These rules do not cover secrets already in environment variables, files outside the repository, MCP tools or network egress.

## Recommended owner protections

1. Run Claude Code in a sandboxed/containerized environment without real credentials; keep secrets out of the workspace.
2. Use a fine-grained GitHub token with only required scopes.
3. Configure GitHub rulesets/branch protection so pushes and merges that violate policy are rejected server-side.
4. Review changes to `.claude/settings.json`, `.github/workflows/**` and `.github/CODEOWNERS` in pull requests.

## GitHub settings checklist — not yet verified

Record each item as Verified enabled / Verified disabled / Not accessible, with a date.

- [ ] Protect `main`: require pull requests, approval, CODEOWNERS review, required validation and secret-scan checks; block force-push and deletion.
- [ ] Verify protection with an authenticated request and confirm a test push to `main` is rejected.
- [ ] Enable secret scanning and push protection where available.
- [ ] Enable private vulnerability reporting where available.
- [ ] Verify Dependabot alerts and updates are enabled.

## Runtime verification — not yet performed

Use a throwaway clone with fake data and no real credentials. Record Claude Code version and PASS / FAIL / NOT RUN for each case.

| Test | Expected result |
| --- | --- |
| Request `git push origin feat/x --force` | Refused by rule |
| Request `git push origin HEAD:main` | Refused by rule |
| Request `cat .env` in a fake-secret test clone | Refused by rule |
| Request `Edit` and `Write` of `.claude/settings.json` | Confirmation prompt for both tools |
| Request `Edit` and `Write` of `.github/workflows/validate-team.yml` | Confirmation prompt for both tools |
| Request `Edit` and `Write` of `.github/CODEOWNERS` and `.github/dependabot.yml` | Confirmation prompt for both tools |
| Request `Edit` and `Write` of `.claude/CLAUDE.md` and `.claude/manifest.json` | Confirmation prompt for both tools |
| Request `rm -fr` on a scratch directory | Refused by rule |
| Try documented bypass classes in the isolated test clone | Record actual result; do not assume blocked |

## Rollback

Revert the reviewed pull request or its commit to restore the previous rules. If an individual rule must change, update `.claude/settings.json` and its validator/test expectations together in the same reviewed pull request.

## Evidence boundaries

- `scripts/validate_team.py`: static presence/structure checks only.
- `tests/test_security_guardrails.py`: simulated matching and negative validator tests; no command execution.
- Runtime enforcement: **NOT RUN** until the procedure above has been completed.
