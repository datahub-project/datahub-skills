# ML impact — reference

How the `datahub-ml-impact` skill decides what breaks, so you can explain any result.

## What "impact" means here

A changed column matters to ML only if something downstream *depends on it*. Blastradar
walks DataHub's lineage from the column to three ML terminal types:

- `mlFeature` / `mlFeatureTable` — the engineered feature derived from the column
- `mlModel` — a model that consumes that feature
- `mlModelDeployment` — a serving deployment of that model

The traversal is a **hybrid** because the graph is heterogeneous (each edge is crossed
the one way DataHub exposes it):

```
changed column (schemaField)
  ├─ column-level lineage ─────────────▶ downstream dataset columns   (propagation)
  └─ table-level lineage + source col ─▶ mlFeature                     (derived_from)
                                           └─ table-level lineage ────▶ mlModel  (consumes)
                                                 └─ aspect read ──────▶ mlModelDeployment
```

It is **deterministic**: the same column always yields the same result (every collection
is sorted; the LLM is only used for prose, never to decide impact). There is a cycle
guard and a hop cap; if the walk is truncated or a column can't be resolved, the result
is marked **incomplete** — which is *not* the same as "no impact."

## Trained-on vs. inference-only — the key distinction

This is what a plain lineage view can't tell you. For each impacted model, Blastradar
reads the model's **training run** (a `dataProcessInstance`) and its
`DataProcessInstanceInput` inputs, and checks whether the **changed dataset** was among
them:

- **Trained on it** → dropping the column corrupts what the model learned. If it's also
  deployed, that's the worst case: a live model silently going wrong.
- **Inference-only** → the model reads the feature at serving time but wasn't trained on
  it; still a real problem (nulls at inference), but a different failure mode.

## Severity rules (deterministic, first match wins)

| Severity | Condition |
|---|---|
| 🔴 critical | `mlModel` with an active deployment **AND** trained on the changed column |
| 🟠 high | `mlModel` with an active deployment (inference-time consumption only) |
| 🟡 medium | `mlModel` with no active deployment |
| ⚪ low | dataset/dashboard with no ML downstream |

Then **escalate one level** (toward critical) if the model carries a `Tier1`/`Critical`
tag or has an owner group. "Active" deployment = status in `IN_SERVICE`, `UPDATING`,
`ROLLING_BACK`. Every finding carries a `reasons` trail so a score is always traceable to
the exact clause that produced it.

## DataHub APIs used (all DataHub Core / open source)

- **Column-level lineage:** `DataHubClient.lineage.get_lineage(source_urn, source_column,
  direction, max_hops)` → `paths[].column_name`.
- **ML entities (aspect reads):** `MLModelPropertiesClass` (`mlFeatures`, `deployments`,
  `trainingJobs`, `groups`), `MLFeaturePropertiesClass` (`sources` + the exact source
  column in `customProperties`), `MLModelDeploymentPropertiesClass` (`status`).
- **Training provenance:** `DataProcessInstanceInputClass` on the model's training run.
- **Resolution / schema:** `get_urns_by_filter` (name → dataset URN, all candidates if
  ambiguous), `get_schema_metadata` (validate the column, expand `SELECT *`).
- **Ownership / tags:** for the escalation rule.

## Reading the output

The runner prints Blastradar's PR-comment markdown (or `--json`). Each finding shows:
severity + model name (+ owner/tags), deployment status, `trained on the changed column`
vs `reads it at inference only`, the lineage path, and a one-line `Why this severity`.
A trailing write-back section shows what *would* be recorded into DataHub (an incident +
`pending-upstream-change` tag per critical/high model, plus one document) — those writes
only happen when `TOOLS_IS_MUTATION_ENABLED=true`.
