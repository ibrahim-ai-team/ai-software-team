# Sprint ROI metrics input

Place one JSON file per sprint at .claude/metrics/sprint-<N>.json, where <N> is a positive sprint number. The report generator reads this file locally and makes no network calls.

## Schema

The top-level value must be an object with a stories array. Each story must provide:

- story_id: non-empty string, such as US-12.
- agent_minutes: non-negative number of elapsed agent work minutes.
- tokens: non-negative number of tokens attributed to the story.
- human_hours_estimated: non-negative estimated human hours needed for equivalent work.

Example:

```json
{
  "sprint": 3,
  "stories": [
    {
      "story_id": "US-12",
      "agent_minutes": 18,
      "tokens": 125000,
      "human_hours_estimated": 2.5
    },
    {
      "story_id": "US-13",
      "agent_minutes": 42,
      "tokens": 210000,
      "human_hours_estimated": 4
    }
  ]
}
```

An empty stories array is valid and produces a report containing **Aucune story**. Invalid JSON, missing fields, wrong field types, negative values, and non-finite numbers produce an error message and exit code 1.

## Calculation

Defaults: --rate-hourly 80 dollars/hour and --token-cost 0.000003 dollars/token.

- Token cost = tokens × token cost per token.
- Estimated human cost = estimated human hours × hourly rate.
- ROI ratio = estimated human cost ÷ token cost.

Example for US-12 above: token cost = 125,000 × $0.000003 = **$0.375**; estimated human cost = 2.5 × $80 = **$200**; ratio = $200 ÷ $0.375 = **533.33**. This ratio compares estimated human cost to token cost only; it is not net profit and excludes agent runtime/infrastructure costs. Record estimates consistently and review them with the sprint team.
