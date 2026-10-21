# Repository security and governance checklist

This starter kit defines instructions and configuration; it is not a security sandbox. Tool allowlists reduce exposure but do not make a broad tool such as `Bash` safe by themselves. Verify the effective permissions in the installed Claude Code version and keep human review for privileged changes.

## Required repository settings

Configure these settings in GitHub **Settings → Rules → Rulesets** (or branch protection, where rulesets are unavailable) for `main`:

- Require a pull request before merging.
- Require at least one approval if the repository has another eligible reviewer; otherwise document the solo-maintainer exception and keep CI required.
- Require the `Static configuration checks (Python 3.10)`, `Static configuration checks (Python 3.11)`, and `Static configuration checks (Python 3.12)` checks.
- Require branches to be up to date before merging when practical.
- Block force pushes and branch deletion.
- Do not allow routine direct pushes to `main`; tightly limit any bypass list.
- Review ruleset bypass actors and GitHub Actions permissions periodically.

A workflow file cannot enable branch protection by itself. Verify the active ruleset in repository settings after configuring it; do not infer enforcement from this document or a green CI run.

## Agent and command permissions

- Give each agent only the tools it needs; keep security review read-only.
- Treat `Bash` as a high-impact capability. Use command restrictions/permission prompts supported by the deployed Claude Code version, and inspect the effective settings.
- Do not place credentials in prompts, tracked files, issue bodies, logs, or test fixtures.
- Treat hooks and text-based secret scanners as defense in depth, not a substitute for secret management or provider-side secret scanning.
- Require human review before merging and before running deployment, destructive, or credential-sensitive commands.

## Secret scanning

Status observed 2026-10-19 (`GET /repos/ibrahim-ai-team/ai-software-team`, `security_and_analysis`):

| Control | What it does | Status |
| --- | --- | --- |
| Gitleaks CI (`.github/workflows/secret-scan.yml`) | Scans history on every push/PR; fails the check | Enabled, green on `main` |
| GitHub secret scanning | GitHub detects provider tokens already pushed and alerts | **Disabled** |
| Push protection | GitHub blocks a push that contains a detected secret | **Disabled** |
| Dependabot security updates | Opens PRs for vulnerable dependencies | **Disabled** |
| Dependabot version updates | Weekly GitHub Actions updates (`.github/dependabot.yml`) | Enabled |

The repository is public, where secret scanning and push protection are available without a paid plan. Enabling them is an owner action (Settings → Code security). Gitleaks only reports after a push; push protection is the only control here that stops a secret before it reaches GitHub. Dependency coverage is complete for this repository: the Python scripts use only the standard library, so GitHub Actions is the only dependency ecosystem. Add ecosystems to Dependabot only when matching manifests (for example `requirements.txt`, `package.json`) exist.

Use GitHub secret scanning / push protection when available for the repository plan. Run an established local scanner (for example, Gitleaks) in CI if the project adopts and pins it. Any custom regex scanner is heuristic and must fail closed when it cannot inspect the repository; it must never report a successful scan after skipping work.

## License

The repository is licensed under the [MIT License](../LICENSE) (owner decision, 2026-10-19, #36). MIT was chosen because it is free, permissive and short, and the kit contains configuration, documentation and small scripts for which a patent grant (Apache-2.0) adds little. Applications created with the kit are separate repositories and choose their own licence (`templates/product-repository/README.md`).

## Verification boundaries

CI covers static repository validation and regression tests only. It does not prove Claude Code runtime discovery/delegation, operating-system sandboxing, GitHub ruleset enforcement, or application behavior. Record actual smoke-test evidence separately in `docs/verification-report.md`.
