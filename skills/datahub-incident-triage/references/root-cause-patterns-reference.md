# Root Cause Patterns Reference

The five ways a data asset breaks, and how to prove each one from DataHub metadata.

## Pattern summary

| Cause type              | One-line description                                           | Primary tool                               |
| ----------------------- | -------------------------------------------------------------- | ------------------------------------------ |
| `schema_drift_upstream` | An ancestor's schema changed and the change propagated         | `list_schema_fields`                       |
| `query_change`          | The transformation that produces the asset was modified        | `get_dataset_queries`                      |
| `upstream_incident`     | An ancestor is already known to be broken                      | `get_entities` (tags)                      |
| `data_source_issue`     | The data is wrong at the source; no transformation is at fault | `get_lineage` to the root + `get_entities` |
| `historical_precedent`  | This exact pattern has happened before                         | `search_documents` (Step 3)                |

Test all of them. Report the ones the evidence supports, ranked. Confidence is not a decoration — it is your estimate of how likely you are to be wrong.

---

## `schema_drift_upstream`

**What it looks like:** a column disappeared, changed type, or became nullable somewhere upstream, and the asset downstream now produces nulls, type errors or missing rows.

**How to detect it:**

1. `get_lineage` upstream to enumerate the ancestors (capped at `max_hops=3`, per Step 5).
2. `list_schema_fields` on the ~5 nearest ancestors, filtered by the field named in the symptom (`keywords=["customer_id"]`). This is one call per ancestor — widen the sweep only if those come back clean.
3. Compare against the same field on the broken asset. Look for: field absent upstream, different type, `nullable: true` where the consumer assumes not-null.

**Evidence to cite:** the ancestor URN, the field path, and what specifically differs. `"urn:li:dataset:(...,raw_orders,PROD)` exposes `customer_id` as nullable; the consumer assumes NOT NULL" is checkable. "Schema drift upstream" alone is not.

**Nuance:** DataHub reflects the last ingestion. A schema that looks fine may have been re-ingested after the fix. Check the asset description and query history for migration notes — teams often record ALTER statements there even when the schema aspect has already caught up.

---

## `query_change`

**What it looks like:** the schema is unchanged but the logic that fills the table changed — a join became a left join, a filter was added, a CASE stopped covering a branch.

**How to detect it:**

1. `get_dataset_queries` on the broken asset.
2. `get_dataset_queries` on its direct parents and on the `dataJob` that writes it.
3. Look for recent queries whose shape differs from the historical pattern: new joins, new filters, changed null handling.

**Evidence to cite:** the query text or fragment, and which asset it writes. Point at the specific clause, not "the query changed".

**Nuance:** query history is sampled from warehouse logs. Absence of a changed query is weak evidence of absence — say so rather than ruling the pattern out.

---

## `upstream_incident`

**What it looks like:** an ancestor is already tagged `incident-degraded` or carries an incident banner in its description, written by a previous triage.

**How to detect it:**

1. Read the batched `get_entities` response Step 5 already took over the full ancestor list — no new call.
2. Check `tags` for `incident-degraded` and `description` for an incident banner.
3. If found, `get_lineage_paths_between` the ancestor and the broken asset to show the propagation path.

**Evidence to cite:** the ancestor URN, the tag, and the path between them.

**Why this pattern matters more than it looks:** it is the system reading its own past actions. A previous run wrote that tag as part of its write-back, and this run consumes it as evidence. It is also the cheapest hypothesis to confirm — the data is already in hand — so test it early. A confirmed upstream incident usually makes the other patterns irrelevant: you have found the real blast origin, and the current asset is a victim, not a cause.

---

## `data_source_issue`

**What it looks like:** the transformation chain is intact — no schema change, no query change — and the bad data is present at the source system itself.

**How to detect it:**

1. `get_lineage` upstream toward the root — usually an operational database, an S3 prefix or an API extract. Extend past the `max_hops=3` cap only for this pattern, and only once the others are ruled out.
2. `list_schema_fields` on the root to confirm the schema is what the pipeline expects.
3. Rule out the other patterns first. This is what remains when nothing in the pipeline changed.

**Evidence to cite:** the root system URN and the fact that every hop between it and the broken asset is unchanged.

**Nuance:** DataHub holds metadata, not data. You can show that the pipeline did not change; you usually cannot show the source rows are wrong. Say that explicitly and phrase the hypothesis as "the pipeline is intact, so the problem most likely originates in the source system" — an inference, not an observation. This is the honest ceiling of a metadata-only diagnosis.

---

## `historical_precedent`

**What it looks like:** a postmortem from Step 3 describes this asset, this symptom, or this cause pattern.

**How to detect it:** it is already done — Step 3 retrieved it. This pattern is where you fold that memory into the ranking.

**Evidence to cite:** the document reference, when the prior incident happened, and how it was resolved.

**How to weigh it:** precedent raises the confidence of whatever pattern it points at; it is rarely the answer by itself. If memory says "last time it was the Postgres source", verify the Postgres source _now_ and report `data_source_issue` with high confidence, citing both the memory and the current check. Reporting `historical_precedent` alone, without re-verifying, is repeating an old answer rather than diagnosing the current incident.

---

## Ranking the hypotheses

Order by confidence, highest first. Calibrate roughly like this:

| Confidence | Meaning                                                                     |
| ---------- | --------------------------------------------------------------------------- |
| 0.80–0.95  | Direct evidence in the metadata plus a plausible propagation path           |
| 0.50–0.79  | Strong circumstantial evidence, or precedent confirmed by a current check   |
| 0.20–0.49  | Consistent with the symptom, not independently confirmed                    |
| below 0.20 | Considered and not supported — worth listing so the reader knows you looked |

Never claim 1.0. Metadata is a lagging, sampled view of a running system.

If two hypotheses are close, report both and say what would separate them — "checking whether the 03:00 dbt run used the new model version would settle this". A next step is more useful than a forced choice.

If nothing is conclusive, say so with low confidence and list what you ruled out. "I checked schema, queries and upstream tags; none show a change. Most likely a source-side issue I cannot confirm from metadata" is a good answer. Inventing a confident cause is not.
