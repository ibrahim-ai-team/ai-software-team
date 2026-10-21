---
name: code-review-refactoring
description: Use when reviewing a diff or refactoring existing code.
---

# Review diffs and refactor safely

## When to use

Use this skill when assessing a PR/diff for defects, maintainability, security implications, regressions, or safe refactoring opportunities.

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
