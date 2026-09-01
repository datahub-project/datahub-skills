# Change Proof Gap Report

## Subject binding

| Property                          | Bound value                        | Source                 | Observed at   |
| --------------------------------- | ---------------------------------- | ---------------------- | ------------- |
| Asset URN and environment         | `<value>`                          | `<DataHub query>`      | `<timestamp>` |
| Schema snapshot                   | `<native version or sha256:value>` | `<schema observation>` | `<timestamp>` |
| Changed field and exact type      | `<canonical path and signature>`   | `<change input>`       | `<timestamp>` |
| Source revision and change digest | `<values>`                         | `<change input>`       | `<timestamp>` |

Binding status: `resolved | unresolved`

An `unresolved` binding mandates an `indeterminate` decision.

## Lineage scope and completeness

- Direction and depth: `<value>`
- Field-lineage query: `<tool and provenance summary>`
- Asset-lineage cross-check: `<tool and provenance summary>`
- Pagination and truncation: `<complete | capped | unknown>`
- Impacted assets and fields: `<count and concise list>`
- Blind spots: `<none or explicit limitations>`

## Proof obligations and evidence status

| Obligation | Impact and risk | Required evidence | Bound evidence             | Status     | Reason    |
| ---------- | --------------- | ----------------- | -------------------------- | ---------- | --------- |
| `PO-001`   | `<value>`       | `<value>`         | `<evidence ID and digest>` | `<status>` | `<value>` |

Allowed statuses: `satisfied`, `negative`, `stale`, `missing`, `unknown`.

## Decision and residual risk

- Decision: `ready | not_ready | indeterminate`
- Deterministic reason: `<rule evaluation>`
- Required gaps: `<obligation IDs>`
- Advisory gaps and residual risks: `<values>`

## Proposed actions

| Action            | Exact target | Safe tool                 | Expected artifact | Side effects and compensation | Idempotency               |
| ----------------- | ------------ | ------------------------- | ----------------- | ----------------------------- | ------------------------- |
| `<proposal only>` | `<target>`   | `<tool or not_available>` | `<artifact>`      | `<value>`                     | `<key or not_applicable>` |

## Human review status

- Status: `not_requested | pending | approved | rejected | expired`
- Decision reference: `<reference or none>`
- Approved payload digest: `<digest or none>`
- Scope changes after approval: `<none or renewed review required>`

## Audit record

```yaml
digest_contract: sha256-stable-json-v1
subject_binding_digest: <digest>
lineage_query_digest: <digest>
obligations_digest: <digest>
evidence_set_digest: <digest>
report_digest: <digest>
decision: <value>
human_review: <status and reference>
action_result: <not_executed | verified | partial | failed | unverified>
previous_event: <digest or null>
recorded_at: <RFC 3339 timestamp>
```

Compute `report_digest` over every report section above except `Audit record`; exclude the digest
field itself.
