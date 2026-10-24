# Telemetry Standard

## Purpose and storage

Telemetry records auditable orchestration events for debugging and delivery evidence. The runtime log is `.claude/telemetry/activity.jsonl`, one JSON object per line (JSON Lines / JSONL). The log is local runtime data and is ignored by Git; do not commit it.

Each event has this schema:

```json
{
  "ts": "2026-10-24T12:00:00+00:00",
  "agent": "agile-orchestrator",
  "action": "delegate",
  "story": "US-123",
  "details": {"target": "qa-automation"},
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agile-orchestrator",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "run_id": "550e8400-e29b-41d4-a716-446655440002",
  "event_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

- `ts`: ISO 8601 timestamp including timezone.
- `agent`: non-empty agent identifier.
- `action`: one of `delegate`, `gate`, `approve`, `tool_call`, or `error`.
- `story`: non-empty story/task identifier, or `"none"` when not associated with a story.
- `details`: JSON object containing minimal, non-sensitive event metadata.
- `trace_id`: UUID version 4, retained for backward compatibility.
- `agent_id`: canonical agent ID from `state/agents.json`; unknown IDs are rejected.
- `session_id`: UUID4 identifying a coordinator session. Pass the same value via `--session-id` or `SESSION_ID` across events in that session; otherwise a new UUID4 is generated per invocation.
- `run_id`: UUID4 identifying a run. Pass the same value via `--run-id` or `RUN_ID` across events in that run; otherwise a new UUID4 is generated per invocation.
- `event_id`: UUID version 4, unique to each event.

## Append-only rules

Use `python scripts/append_telemetry.py --agent ... --action ... --story ... --details '<json-object>'` to write events. Use `--agent-id` (or `AGENT_ID`) for canonical identity; the existing `--agent` argument remains supported. The writer creates the directory and file when needed and appends exactly one line; it must never truncate or rewrite existing events. Invalid JSON, invalid fields, or sensitive field names fail with exit code 1 and do not append a record.

Never log secrets, credentials, tokens, passwords, API keys, private keys, session cookies, personal data, or private chain-of-thought. Reject any details key containing `token`, `password`, `api_key`, or `secret` (case-insensitive), including nested keys. Keep details concise and operational. Do not pass secret values to the command in the first place.

## Event guidance

- `delegate`: record the story/task ID and delegated agent/role.
- `gate`: record the gate name, outcome, and evidence reference; do not claim success without evidence.
- `approve`: record the approval decision and authority.
- `tool_call`: record tool name and a short outcome, not full payloads.
- `error`: record a safe error category and recovery reference, not raw secret-bearing exceptions.

## Analysis

Run `python scripts/analyze_telemetry.py` to summarize event counts per agent, error count, elapsed duration per story, gate events, and legacy event count. Records missing one or more of `agent_id`, `session_id`, `run_id`, or `event_id` remain readable and are counted as legacy. Duration is calculated as the time between the first and last valid event for each story; stories with fewer than two events have a duration of zero. The analysis reports gate events as recorded, not as proof that a gate was passed. Empty or missing logs produce a valid zero-event summary.

The log is append-only by convention and tooling, not tamper-proof. Treat it as operational evidence and review changes to the writer and its tests.

## Scope enforcement denials

Every refused agent-scope check should emit a telemetry event with `action=error` and `details.refused_path` set to the denied repository-relative path. Do not log file contents, credentials, or other secrets.
