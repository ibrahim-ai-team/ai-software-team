# Mechanical Validation Gates

## Authority: Gate versus Checkpoint

**Gate = agent; Checkpoint = human.** G1/G2 are produced by agents using evidence and the schemas in this standard. CP1–CP4 are explicit human decisions recorded under `.claude/approvals/` and checked by `scripts/check_approvals.py` as defined in `standards/human-in-the-loop.md`. A passing Gate never replaces a human Checkpoint, and a Checkpoint never replaces technical verification.

## Gate 1 (G1) — Pre-execution plan review

Before any coding agent starts implementation, `code-review-security` reviews the proposed plan for a clear scope, exact expected files/paths, tests and verification commands, and material risks/mitigations. The plan artifact must contain all four areas. The reviewer records the SHA-256 digest of the exact plan reviewed.

Output file: `.claude/gates/G1-<story>.json`

Schema and complete example:

```json
{
  "passed": true,
  "reviewer": "code-review-security",
  "date": "2026-10-24T12:00:00Z",
  "plan_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

The hash is illustrative; use the actual SHA-256 digest of the reviewed plan. A Gate passes only when `passed` is the boolean `true`, `reviewer` is exactly `code-review-security`, `date` is an ISO 8601 date-time with timezone, and `plan_hash` is 64 hexadecimal characters. No coding agent may begin before G1 passes.

Check with: `python scripts/check_gates.py --story <story> --gate G1`.

## Gate 2 (G2) — Post-execution verification

After implementation and before the change can be approved for merge, `ci-verifier` executes applicable allowlisted checks and returns factual JSON. `code-review-security` (read-only, without Bash) judges that evidence against the actual diff. **G2 is an objective fact from ci-verifier plus an independent judgment from code-review-security; both must agree for G2 to pass.** A skipped, missing, malformed, failed, or disputed mandatory check blocks G2. The verifier never persists to `.claude/gates/`; only the orchestrator persists after reviewer approval. If verifier and reviewer diverge, escalate to the human sponsor at CP3. The required evidence covers:

1. **Lint:** the required lint/format checks completed successfully.
2. **Tests:** the applicable automated test suite completed successfully.
3. **Secrets:** repository/diff secret scanning completed successfully with no finding requiring remediation.

Output file: `.claude/gates/G2-<story>.json`

Schema and complete example:

```json
{
  "passed": true,
  "reviewer": "code-review-security",
  "date": "2026-10-24T12:30:00Z",
  "checks": {
    "lint": "pass",
    "tests": "pass",
    "secrets": "pass"
  },
  "commit": "0123456789abcdef0123456789abcdef01234567"
}
```

A Gate 2 passes only if `passed` is the boolean `true`, the reviewer and date are valid, all three check values are exactly `pass`, and `commit` is the full 40-character SHA that `ci-verifier` tested and the reviewer judged. The checker compares it with the commit being merged (`--commit <PR head SHA>`, or `git rev-parse HEAD` when omitted); any later commit needs a new G2. A failed, missing, unknown, or incomplete check makes G2 invalid. Never mark a check as passed without its actual output/evidence. No merge may proceed without G2 passing and human CP3 approval.

Check with: `python scripts/check_gates.py --story <story> --gate G2 --commit <PR head SHA>`.

## Required ordered flow

`CP1 → G1 → code → ci-verifier facts → code-review-security judgment → persist G2 → CP3 → merge`

- **CP1:** human approves the plan.
- **G1:** `code-review-security` validates the plan mechanically and records the result.
- **Code:** implementation agents may work only after both CP1 and G1 pass; CP2 architecture approval is also required where defined by the HITL standard.
- **G2:** lint, tests, and secret scanning all pass.
- **CP3:** human approves the reviewed code before merge.
- **Merge:** the repository owner/human merges. Agents do not merge.

Before each lifecycle transition, the orchestrator checks the relevant gate with `scripts/check_gates.py` and the relevant human checkpoint with `scripts/check_approvals.py`. If either check fails, stop and report the missing evidence; do not bypass or fabricate a result.

## Checker contract and limitations

`scripts/check_gates.py` is standard-library-only and read-only. It returns 0 for a valid passing record, 1 when the record is absent or invalid (including a failed check), and 2 for a missing or invalid `--gate` argument. It validates schema and digest format; it does not recompute `plan_hash` against the plan because no plan path is supplied, and the JSON record does not prove reviewer identity. Preserve the underlying CI logs/review evidence and repository access controls.
