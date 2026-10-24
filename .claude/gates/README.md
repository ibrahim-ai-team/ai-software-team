# Validation Gate Records

Gate result files are stored as `.claude/gates/G1-<story>.json` or `.claude/gates/G2-<story>.json`. See `standards/validation-gates.md` for the full policy, required evidence, and examples.

- G1 records the pre-execution plan review: `passed`, `reviewer`, ISO 8601 `date`, and SHA-256 `plan_hash`.
- G2 records post-execution results: `passed`, `reviewer`, ISO 8601 `date`, and `checks.lint`, `checks.tests`, `checks.secrets`, each exactly `pass`.

Check a record with:

```bash
python scripts/check_gates.py --story SHOP-12 --gate G1
python scripts/check_gates.py --story SHOP-12 --gate G2
```

Exit codes: 0 = valid and passing; 1 = absent or invalid record; 2 = missing or invalid gate argument. The checker only reads gate files and never creates or modifies them. Agents produce G1/G2; humans produce CP1–CP4. Do not use a gate result as a substitute for human approval.
