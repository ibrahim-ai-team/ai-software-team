---
description: Display persisted effective status for humans or scripts
---

# Status

Run the status report against the persisted `state/effective.json` snapshot:

```bash
python scripts/status_report.py
```

Options:

- `--json`: emit the effective snapshot as JSON on stdout, suitable for pipes (for example, `python scripts/status_report.py --json | python -m json.tool`).
- `--filter agent=AGENT_ID`: show one agent, matched against `agent_id` (case-insensitive).
- `--filter task=TASK_ID`: show one task, matched against `task_id` (case-insensitive).

The default output is a compact human-readable table. The report reads only `state/effective.json`; it does not reconstruct status from `project-state.md` or telemetry. If the snapshot is missing, unreadable, or older than one hour, the command warns and still exits successfully so callers can inspect the available state. A stale snapshot is marked explicitly with its age.
