# Human Approval Records

Each human decision is a separate JSON file that **the human creates** (in an editor or terminal). Claude cannot write these files: `.claude/settings.json` denies edits to `.claude/approvals/*.json` and `.claude/human-approvers.json`, no agent scope covers `.claude/`, and the scope hook blocks shell writes. The orchestrator only asks for the approval and verifies it.

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

## Approver list

Create `.claude/human-approvers.json` to bind approvals to people:

```json
{ "approvers": ["your-github-username"] }
```

When it exists, `approved_by` in approval records, `human_decision.decided_by` in disagreement records and `approved_by` in provisioning records must exactly match a listed username (case-insensitive). A malformed or empty list fails closed: no approval is accepted. Without the file, disagreement records accept only `human sponsor`, `sponsor` or `human`.

## Provisioning approval

Before `python3 scripts/provision_project.py apply <plan>` creates anything, the sponsor creates `.claude/approvals/PROVISION-<project-id>.json` with `approved_by` and `plan_digest` set to the full digest printed by `provision_project.py plan`. The plan file's own approval block is not enough, because whoever writes the plan can fill it in.

**Security boundary:** this JSON is an auditable record, not proof of identity. The checker validates the digest's SHA-256 format but cannot recompute it against the artifact because no artifact path is supplied. Human approval authority must be enforced through repository permissions and review controls.
