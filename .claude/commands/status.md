---
description: Display persisted effective status and validate its health
---

# Status

Run the status report against the persisted `state/effective.json` snapshot:

```bash
python scripts/status_report.py
```

Options:

- `--json`: emit the effective snapshot JSON on stdout for backward-compatible consumers. This alone does **not** prove the snapshot is valid or fresh.
- `--health-json`: emit a health envelope with `status_health`, `snapshot_valid`, `snapshot_age_seconds`, `source`, `problems`, and `snapshot`.
- `--strict`: exit non-zero if the snapshot is missing, malformed, schema-invalid, contains duplicate/invalid entity IDs, is stale (one hour or more), or has a timestamp more than five minutes in the future.
- `--filter agent=AGENT_ID`: show one agent, matched against `agent_id` (case-insensitive).
- `--filter task=TASK_ID`: show one task, matched against `task_id` (case-insensitive).

The default output is a human-readable diagnostic table and remains tolerant so humans can inspect available state. For any automation that makes a workflow decision, use `--health-json --strict` and treat a non-zero exit code as a stop condition. The report reads only `state/effective.json`; it does not reconstruct status from `project-state.md` or telemetry. It cannot establish Claude Code runtime discovery or delegation.
