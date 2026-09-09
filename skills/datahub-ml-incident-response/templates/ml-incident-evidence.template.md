# ML incident evidence report

## Incident

| Field | Value |
| --- | --- |
| Type | `<freshness | desync | replay | partial-backfill | late-event | stale-lineage | unclassified>` |
| Confidence | `<verified | degraded | incomplete>` |
| Affected event-time range | `<start to end>` |
| Source evidence | `<watermark, parity values, event counts, manifest, or job record>` |

## Verified DataHub context

| Asset | URN | Type | Owner | Hop | Evidence |
| --- | --- | --- | --- | --- | --- |
| `<asset>` | `<verified URN>` | `<dataset | feature | model | job>` | `<owner or missing>` | `<n>` | `<schema, lineage, or deployment evidence>` |

## What breaks and why

1. `<asset>` — `<failure mode>`
2. `<asset>` — `<failure mode>`

**Incomplete or stale evidence:** `<none, or what must be re-read before a conclusion>`

## Remediation and controlled resume

- **Fix first:** `<bounded remediation>`
- **Owner route:** `<team or missing-owner escalation>`
- **Validate:** `<specific verification>`
- **Rollback:** `<reversal or publication pause>`
- **Resume only when:** `<objective condition>`

## Dry-run writeback

```json
{
  "dry_run": true,
  "target": "<DataHub entity or GitHub issue>",
  "incident_type": "<type>",
  "verified_urns": ["<URN>"],
  "owner_route": ["<owner>"],
  "remediation": "<bounded fix>",
  "validation": ["<check>"],
  "rollback": "<condition>"
}
```

No live mutation is permitted until a human approves this exact payload and the post-write verification plan.
