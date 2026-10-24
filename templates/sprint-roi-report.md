# Sprint {{sprint}} — ROI report

## Summary

| Story ID | Agent time (min) | Tokens | Token cost ($) | Estimated human hours | Estimated human cost ($) | ROI ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| {{story-id}} | {{agent-minutes}} | {{tokens}} | {{token-cost}} | {{human-hours}} | {{human-cost}} | {{roi-ratio}} |

## Method

- **Token cost ($)** = tokens × token cost per token (default: 0.000003 USD).
- **Estimated human cost ($)** = estimated human hours × hourly human rate (default: 80 USD/hour).
- **ROI ratio** = estimated human cost ÷ token cost. A ratio above 1 means the estimated human equivalent costs more than the measured token cost. This ratio compares only estimated human cost with token cost; it excludes agent runtime and other infrastructure costs.
- Agent time is reported in minutes and is not converted into token cost.
- Monetary values are rounded to 6 decimal places for token cost and 2 decimal places for human cost. The ratio is displayed to 2 decimal places; when token cost is zero and human cost is positive, it is shown as infinity (if both are zero, 0.00).
- The report uses only the local input file .claude/metrics/sprint-{{sprint}}.json. It makes no network calls.
