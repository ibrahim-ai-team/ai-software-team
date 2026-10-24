# Human Approval Records

The orchestrator records each human decision in a separate JSON file:

`.claude/approvals/CP<N>-<story>.json`

`<N>` is 1–4 and `<story>` is the story identifier, for example `SHOP-12`. The file must contain these fields:

- `checkpoint`: one of `CP1`, `CP2`, `CP3`, `CP4`.
- `story`: exact story identifier matching the filename and checker argument.
- `approved_by`: non-empty GitHub username of the human approver.
- `date`: ISO 8601 date-time with timezone, such as UTC `Z` or `+00:00`.
- `artifact_hash`: 64 hexadecimal characters representing the SHA-256 digest of the exact artifact reviewed at this checkpoint.

## Complete example

Example file: `.claude/approvals/CP1-SHOP-12.json`

```json
{
  "checkpoint": "CP1",
  "story": "SHOP-12",
  "approved_by": "ibrahim-ghorafi",
  "date": "2026-10-24T12:00:00Z",
  "artifact_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

The digest above is illustrative; replace it with the actual SHA-256 digest of the approved artifact. Do not use the example as a real approval.

Verify a decision with:

```bash
python scripts/check_approvals.py --story SHOP-12 --checkpoint CP1
echo $?
```

Exit code `0` means the approval record is structurally valid for the requested story/checkpoint. Exit code `1` means it is absent or invalid. Exit code `2` means required arguments or argument values are invalid. The checker is read-only.

**Security boundary:** this JSON is an auditable record, not proof of identity. The checker validates the digest's SHA-256 format but cannot recompute it against the artifact because no artifact path is supplied. Human approval authority must be enforced through repository permissions and review controls.
