---
description: Review a pull request for correctness, security, and evidence
---

# Review PR

Use `tech-lead` for the technical review (correctness, design, maintainability, tests) and `code-review-security` for the independent read-only security assessment. Neither may review work it authored. Select `code-review-refactoring`, `security-threat-modelling`, and `git-github-workflows` skills as applicable.

1. The coordinator must obtain the actual diff for the target PR and pass the diff, changed-file list, requirements/acceptance criteria, and observed CI/test results to the delegated read-only reviewer. Do not ask the reviewer to infer a diff it cannot access.
2. Each reviewer follows its own agent checklist against the supplied evidence (diff, target branch, linked story, changed-file scope), including edge cases, backwards compatibility and test adequacy.
3. Run available relevant checks in the coordinating session; separate checks that ran from checks not available or not run, and give the reviewer the exact commands and observed outcomes.
4. Report findings first, ordered by severity, with file/line references and concrete remediation.
5. Verify acceptance criteria and Definition of Done against observable evidence.
6. Do not merge the PR, change branch protections, or claim CI is green without observing the result.
