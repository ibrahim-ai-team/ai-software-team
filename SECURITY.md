# Security Policy

## Supported versions

Security fixes are considered for the current default branch. This starter kit is provided as-is; runtime safety depends on the installed Claude Code version, its permission settings, and the surrounding environment.

## Reporting a vulnerability

Please do not publish secrets, tokens, personal data, or exploitable details in a public issue. Use GitHub's private vulnerability reporting feature if it is enabled for this repository. If it is unavailable, contact the repository owner privately through an established channel.

Include the affected file/version, impact, reproducible steps that do not expose secrets, and a suggested mitigation when possible.

## Licences

Generated or reused code can reproduce protected expression, and generated code is not automatically license-free. The repository policy prohibits GPL-3.0 and AGPL dependencies/source by default, requires provenance review for additions over 50 lines, and blocks dependencies whose license cannot be verified. See [License Risk Standard](standards/license-risk.md) and the automated [dependency license workflow](.github/workflows/license-check.yml). Exceptions require documented owner approval and compatibility review.

## CI/CD

GitHub Actions workflows must use explicit least-privilege permissions, pin third-party Actions to full commit SHAs, disable persisted checkout credentials unless required, validate untrusted inputs, and keep PR workflows read-only. No workflow may use `permissions: write-all`. See [CI/CD Hardening Standard](standards/ci-cd-hardening.md). The `PROJECTS_TOKEN` used by the Project status workflow is a separate secret and must be scoped independently from `GITHUB_TOKEN` permissions.

## Scope and limitations

- Static validation is not a security certification.
- Local Claude Code deny rules are defense-in-depth, not a security sandbox.
- GitHub branch protection, secret scanning, and push protection require separate repository-owner configuration.
- Never test against systems or credentials you do not own or have explicit permission to assess.
- See [Security Guardrails](docs/security-guardrails.md) for the threat model, known bypasses, and the runtime verification procedure.
