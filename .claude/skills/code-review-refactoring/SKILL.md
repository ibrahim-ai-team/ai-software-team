---
name: code-review-refactoring
description: Reviews diffs for correctness and maintainability with severity-ranked, file:line findings, and refactors without changing behavior. Use when reviewing a pull request diff or refactoring existing code.
disable-model-invocation: true
---

# Review diffs and refactor safely

## When to use

Use this skill when assessing a PR/diff for defects, maintainability, security implications, regressions, or safe refactoring opportunities.

## Required inputs

The actual diff or PR head commit, the linked issue and acceptance criteria, CI results, and the author (the reviewer must not be the author).

## Procedure

Review actual changes for correctness, readability, coupling, duplication, testability, and regressions. Report evidence-based findings with severity and file/line. Refactor in small steps and rerun relevant checks.

## Expected outputs

- Findings ordered by severity with file/line and supporting evidence
- Missing tests, risks, and checks not run
- Minimal remediation suggestions and an explicit review disposition recommendation

## Quality checks

- Review the actual diff and linked evidence; missing evidence means BLOCKED, not assumed PASS.
- Separate confirmed defects from questions and stylistic preferences.
- Do not claim tests ran unless output or CI evidence is available.
