---
name: datahub-ml-impact
description: >
  Assess the ML impact of a data change using the DataHub context graph: walk
  column-level lineage from a changed dataset to every affected feature,
  model, and deployment; score severity; and check features for structural
  target leakage. Use when asked "which models are affected by this change",
  "what's the blast radius of X", "is it safe to retrain", or "check this
  model for target leakage".
---

# DataHub ML impact analysis

You have access to a DataHub instance through its MCP server (`search`,
`get_lineage`, `get_entities`, `list_schema_fields`, `get_dataset_queries`).
This skill turns those primitives into an ML-aware impact assessment.

## When to use

- A dataset or column changed (schema change, migration, backfill) and the
  user wants to know which ML assets are affected.
- Before a retrain/deploy: "is the supply chain of this model healthy?"
- A model behaves suspiciously well: "does any feature contain the answer?"

## Walking the blast radius

1. Resolve the changed dataset with `search`; confirm the exact URN before
   using it — never guess URNs.
2. `get_lineage` with `upstream=false`, `max_hops=6`. Do the discovery walk at
   **table level** (complete and robust), then refine to column level with the
   `column` parameter where fine-grained lineage exists. Real-world
   column-level lineage is partial: when a hop has no column edge but both
   sides share a column name, treat it as a passthrough and say so
   ("confidence: table-level" vs "column-level").
3. Collect every `mlFeature`, `mlModel`, and `mlModelDeployment` reached.
   Deployments usually hang off the model's properties rather than lineage —
   `get_entities` on each model to resolve them and their environment.
4. Fetch owners of every affected node — they are the notification list.
5. Pull the captured/compiled SQL of affected transformations
   (`get_dataset_queries` or the dataset's view definition) and check whether
   the changed column is actually referenced. A change that is never
   referenced downstream is cosmetic, whatever the lineage says.

## Severity rubric

| Severity | Condition |
|---|---|
| P0 | breaking change (rename/drop/type-narrowing of a referenced column) with a **deployed production** model downstream |
| P1 | breaking + referenced with any deployed model downstream, OR a semantic shift (type-compatible but meaning changed — e.g. dollars to cents) with a production deployment |
| P2 | breaking/semantic + referenced; models downstream but none deployed |
| P3 | cosmetic, additive, or unreferenced |

Call out semantic shifts explicitly: a float→integer narrowing on a column
whose name loses a unit suffix (`amount_usd` → `amount`) usually means a unit
change that no compiler will catch.

## Structural target-leakage check

For each feature the model consumes, walk lineage **backwards** and ask:

- **L1 (direct)**: does any upstream column path include the model's label
  column? → leak.
- **L2 (temporal)**: does any path cross an asset that records post-outcome
  events (chargebacks, refunds, resolutions — anything timestamped after the
  prediction moment)? Tagging such assets (e.g. `post-outcome`) makes this
  check mechanical. → leak.
- **L3 (window)**: does the feature's defining SQL use forward-looking time
  arithmetic past the prediction timestamp (`event_ts + interval`,
  `dateadd(...)`, `lead(...)`)? Trailing windows (`- interval`) are fine. →
  suspect; read the SQL to confirm.

This is structural, not statistical: it needs only lineage and captured SQL,
no access to the data. Report the rule that fired and the exact lineage path
as evidence, and be honest that absence of a signal is not proof of absence.

## Writing back

Leave what you learned in the graph so the next agent inherits it: append the
assessment to the model's documentation, and raise an incident with the
evidence directly on the ML entity that is at risk. `mlModel`, `mlFeature`,
and `mlFeatureTable` all take incidents, and one incident can carry several
urns, so name the model, the affected features, and the upstream dataset in
a single incident instead of filing on the dataset and hoping the reader
connects it to the model. That incident is now the model-side signal, so a
`model-at-risk` tag is no longer needed to stand in for one.

Against releases that predate this support (v1.7.0 and earlier), incidents do
not surface on ML entities, and the older pattern still applies: file on the
affected upstream dataset and tag the models (`model-at-risk`,
`leakage-suspect`). `mlModelGroup` and `mlModelDeployment` take no incidents
on any release yet, so raise on the model.
