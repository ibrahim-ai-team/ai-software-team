# Human-in-the-Loop Approval Standard

## Purpose and authority

Human-in-the-loop (HITL) checkpoints are mandatory sponsor decisions at lifecycle boundaries. They are distinct from automated agent Gates: a Gate is evidence that an agent or script checked a technical condition; a Checkpoint (CP) is an explicit human approval. A passing Gate never substitutes for a CP, and a CP never substitutes for a Gate.

Every approval is recorded as `.claude/approvals/CP<N>-<story>.json`. The orchestrator must run `python scripts/check_approvals.py --story <story> --checkpoint CP<N>` before crossing the corresponding boundary. Exit code 0 permits that transition; exit code 1 means approval is absent or invalid and the orchestrator must stop; exit code 2 means the checker was invoked with missing or invalid arguments and must be corrected. The checker is read-only.

Only the human creates approval records: `.claude/settings.json` denies Claude edits to `.claude/approvals/*.json` and `.claude/human-approvers.json`, and no agent scope covers `.claude/`. When `.claude/human-approvers.json` exists, `approved_by` must exactly match a listed username; a malformed or empty list fails closed (`.claude/approvals/README.md`).

`approved_by` records the human approver's GitHub username. The approval JSON is an auditable record, not cryptographic identity proof: repository permissions and review history remain the source of authority. `artifact_hash` must be the SHA-256 hex digest of the exact artifact reviewed for that checkpoint. The checker validates its SHA-256 representation; since the CLI receives no artifact path, it cannot independently recompute the digest from the source artifact.

## Mandatory checkpoints

### CP1 — Plan approval

- **When:** after the delivery plan and backlog/sprint proposal are prepared, before any application code is written.
- **Who approves:** the human sponsor; an agent cannot approve on their behalf.
- **Approval artifact:** `.claude/approvals/CP1-<story>.json`, with `artifact_hash` set to the SHA-256 digest of the approved plan.
- **Blocked agent/action:** the agile orchestrator is blocked from dispatching implementation work or authorizing code changes until approval is valid.
- **Verifier:** `python scripts/check_approvals.py --story <story> --checkpoint CP1`.

### CP2 — Architecture approval

- **When:** after architecture and relevant ADRs are prepared, before implementation begins.
- **Who approves:** the human sponsor; architect and Tech Lead recommendations are not approvals.
- **Approval artifact:** `.claude/approvals/CP2-<story>.json`, with `artifact_hash` set to the SHA-256 digest of the approved architecture package/ADR.
- **Blocked agent/action:** implementation agents (including backend, frontend, database, and DevOps specialists) are blocked from starting implementation.
- **Verifier:** `python scripts/check_approvals.py --story <story> --checkpoint CP2`.

### CP3 — Code approval

- **When:** after implementation, automated checks, QA and review evidence are available, before merge.
- **Who approves:** the human sponsor/repository-authorized human reviewer. Agent reviews are supporting evidence only.
- **Approval artifact:** `.claude/approvals/CP3-<story>.json`, with `artifact_hash` set to the SHA-256 digest of the exact reviewed code/diff artifact.
- **Blocked agent/action:** the agile orchestrator is blocked from declaring the change approved for merge or merging it; the human retains merge authority.
- **Verifier:** `python scripts/check_approvals.py --story <story> --checkpoint CP3`.

### CP4 — Release approval

- **When:** after release readiness evidence is assembled, before creating a version tag or publishing a release.
- **Who approves:** the human sponsor/release authority.
- **Approval artifact:** `.claude/approvals/CP4-<story>.json`, with `artifact_hash` set to the SHA-256 digest of the release candidate/readiness artifact.
- **Blocked agent/action:** release-manager and DevOps agents are blocked from creating tags, publishing releases, or deploying the release until approval is valid.
- **Verifier:** `python scripts/check_approvals.py --story <story> --checkpoint CP4`.

## Operational rules

- Check the relevant checkpoint immediately before every transition that crosses its boundary; do not treat a previous checkpoint as approval for a later one.
- A missing, malformed, mismatched, or invalid approval means STOP and request the human decision. Never create approval records on the human's behalf.
- Use a safe story identifier in filenames; the checker rejects path traversal and unsupported characters.
- Do not commit secrets or sensitive personal information in approval records.
- This mechanism validates the approval record's schema and hash format. It does not authenticate the username, compare the digest with an external artifact, or prove that the recorded person actually clicked approve; enforce human authority through repository access and review controls.
