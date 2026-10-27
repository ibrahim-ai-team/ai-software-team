---
name: docker-cicd
description: Builds repeatable, least-privilege container and CI workflows with pinned dependencies. Use when changing containers, CI pipelines, builds or delivery workflows.
---

# Build repeatable container and CI workflows

## When to use

Use this skill for Docker/container configuration, CI workflows, build pipelines, deployment automation, or environment setup.

## Required inputs

The current workflow/container files, the required checks, the target environment, and the permissions and secrets policy (names only, never values).
## Procedure

Use reproducible builds, minimal base images, non-root execution, pinned or controlled dependencies, health checks, caching where safe, and least-privilege CI permissions. Never expose secrets in logs or images.

## Expected outputs

- Reproducible build/pipeline or container configuration changes
- Verification steps and expected outcomes
- Permissions, secret handling, operational risks, and rollback notes

## Quality checks

- Use least-privilege workflow permissions and protect secrets from logs/images.
- Prefer pinned or controlled dependencies and minimal non-root images where applicable.
- Do not deploy, publish, or create billable infrastructure without explicit authorization.
