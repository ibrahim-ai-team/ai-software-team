# Local telemetry log

This directory stores local runtime telemetry. The append-only log `activity.jsonl` is intentionally ignored by Git and must not be committed.

Append an event from the repository root:

```bash
python scripts/append_telemetry.py \
  --agent agile-orchestrator \
  --action delegate \
  --story US-123 \
  --details '{"target":"qa-automation"}'
```

Analyze the log:

```bash
python scripts/analyze_telemetry.py
```

The writer adds an ISO 8601 timestamp and UUID4 trace ID. It rejects invalid JSON and nested detail keys containing `token`, `password`, `api_key`, or `secret`. Never pass secret values to telemetry commands. See [the telemetry standard](../../standards/telemetry.md) for the schema, event guidance, and limitations.
