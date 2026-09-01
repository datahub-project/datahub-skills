# Protocol Reference (condensed)

Quick-lookup version of `protocol/SPEC.md` §3–4 for use mid-task. The normative source is
`protocol/SPEC.md`. If this file and SPEC.md ever disagree, SPEC.md wins.

---

## The five learning kinds (SPEC.md §3)

Every learning has exactly one `kind`. Do not invent new kinds: v1 is a fixed set.

| Kind                | Use when                                                                                                                              | One-line example                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `semantic_gotcha`   | A value's unit, encoding, or scope differs from what its name/type implies.                                                           | `amount` is in cents, not dollars.                                         |
| `verified_query`    | Getting a correct answer required combining several non-obvious fixes and re-deriving that combination is expensive.                  | The exact SQL for "monthly revenue," confirmed against a dashboard.        |
| `join_path`         | Two plausible join keys exist and one is broken, deprecated, or silently drops/duplicates rows.                                       | Join on `customer_key`, not `customer_id` (47% NULL).                      |
| `caveat`            | The data is correct as far as it goes but incomplete, stale, or scope-restricted in a way that matters.                               | Table only contains `us-east` orders; international orders live elsewhere. |
| `metric_definition` | A named business metric (revenue, active users, churn) has more than one plausible SQL definition and one has been confirmed correct. | "Revenue" excludes cancelled/refunded orders.                              |

## The learning record schema (SPEC.md §4)

| Field            | Required                   | Notes                                                                                                   |
| ---------------- | -------------------------- | ------------------------------------------------------------------------------------------------------- |
| `id`             | yes                        | UUID4, assigned once at creation, never changes.                                                        |
| `kind`           | yes                        | One of the five above.                                                                                  |
| `subject_urn`    | yes                        | The dataset entity urn.                                                                                 |
| `subject_field`  | optional                   | Column name within `subject_urn`, if column-scoped. Omit for table-level.                               |
| `claim`          | yes                        | 1–2 sentences, ≤280 chars. Longer usually means two learnings.                                          |
| `evidence`       | yes                        | Concrete and checkable: a query + result, a count, a named comparison. Never "seems right." ≤500 chars. |
| `confidence`     | yes                        | `high` \| `medium` \| `low`; see below.                                                                 |
| `learned_by`     | yes                        | `<agent-name>/<session-id>`.                                                                            |
| `learned_at`     | yes                        | `YYYY-MM-DD`.                                                                                           |
| `status`         | optional, default `active` | `active` \| `disputed` \| `conflict`.                                                                   |
| `conflicts_with` | optional                   | Present only when `status: conflict`; the `id` of the disputed record.                                  |

Serialization: one learning = one single-line JSON object (omit absent optional fields), one JSON string per value in the `io.datahub.agentMemory.learnings` structured property's value list.

## Confidence: honest definitions, applied as written (SPEC.md §4, §6)

| Level    | Definition                                                                                  | Applied during recall as                                                                        |
| -------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `high`   | Verified against an independent, trusted source and matched.                                | Apply directly, no re-derivation.                                                               |
| `medium` | Internally consistent and compelling, but not independently cross-checked.                  | Apply provisionally + one cheap targeted check before relying on it for a consequential answer. |
| `low`    | A plausible explanation, not tested. Rare; a learning this weak is often not worth writing. | Hint only; independently verify before treating as true.                                        |

## Structured property definition (SPEC.md §5.1)

```yaml
id: io.datahub.agentMemory.learnings
type: string
cardinality: MULTIPLE
entityTypes: [dataset, schemaField]
```

Registered once via `setup/register_properties.py`: no MCP tool defines property schemas, only assigns values to properties that already exist.
