---
name: git-github-workflows
description: Makes safe, reviewable Git changes on feature branches and pull requests, never on the default branch. Use when branching, committing, opening PRs or managing GitHub changes.
---

# Make safe and reviewable Git changes

## When to use

Use this skill for repository changes, branch/commit strategy, pull requests, CI review, or GitHub coordination.

## Required inputs

The target repository and branch, the linked issue, the base branch state, and the permission boundary (no merge, no push to the default branch). If a required input is missing, stop and ask the orchestrator for it instead of assuming it.

## Procedure

Inspect status and diffs before changes. Use focused branches and descriptive commits, avoid committing secrets, never rewrite shared history without approval, and report checks skipped. Push only when explicitly authorized.

## Expected outputs

- Focused branch/commit/PR references and changed-path summary
- Exact checks run and checks skipped with reasons
- Review/merge state and follow-up actions, based on observed GitHub evidence

## Quality checks

- Inspect status and diff before committing; keep unrelated changes out.
- Never place tokens/secrets in commits and never rewrite shared history without approval.
- Push only when authorized; never merge or enable auto-merge on the user's behalf.
