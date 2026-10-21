---
name: git-github-workflows
description: Use when branching, committing, opening PRs, or managing GitHub changes.
---

# Make safe and reviewable Git changes

## When to use

Use this skill for repository changes, branch/commit strategy, pull requests, CI review, or GitHub coordination.

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
