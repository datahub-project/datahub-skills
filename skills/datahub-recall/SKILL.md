---
name: datahub-recall
description: |
  Trace a data defect forward to the models and deployments that learned from it,
  then write a scoped recall back into DataHub. Use when a source (sensor, vendor,
  feed, pipeline) produced bad data over a period and you need to know what to
  stop — or when someone asks "which models were trained on this?" or "where is
  that model running?". Covers the dataset→model→deployment hops that DataHub's
  lineage graph does not currently traverse via get_lineage.
user-invocable: true
---

# Recall — forward blast radius for data defects

## When to use this

A data source went bad for a while and nobody noticed at the time. Something
downstream is now misbehaving. The question is **which deployed things learned
from the bad data** — and which ones did not.

Triggers: miscalibrated sensors, collapsed vendor label quality, corrupt datasets,
"can we put these machines / endpoints back into service yet?"

## Critical context: the lineage gap

**DataHub's lineage graph stops at the dataset layer** for agent tooling.

Measured on GMS v1.6.0 with ML entities loaded (ACK `get_lineage` /
`searchAcrossLineage`, `skipCache: true`):

| Traversal | Hops |
|---|---|
| source → batches | works |
| batch → dataset | works |
| dataset → upstream batches | works |
| **dataset → model** | **0** |
| **model → deployment** | **0** |

The edges *are* stored in aspects (`mlModelTrainingData`,
`MLModelProperties.deployments`). They are not projected into the lineage graph
agents traverse, and `MLModelDeployment` is not a GraphQL entity type.
Upstream tracking: https://github.com/datahub-project/datahub/issues/19061

**Do not treat an empty `get_lineage` on a model as "no impact."** That is the
gap, not the answer. Read aspects URN-direct for the ML hops.

## Workflow

### 1. Bound the defect window (DataHub ACK / MCP)

- `search` — find candidate sources
- `get_entities` — maintenance history often brackets the fault
- `get_lineage(upstream=false)` — list batches a source produced
- `get_entities` on batches — quality metrics; find first/last bad day

Prefer **two independent signals** (maintenance record + readings). The window
is the single input that determines blast radius.

### 2. Cross the ML hops via aspects (not get_lineage)

For each contaminated training dataset URN:

1. Find models that list it in `mlModelTrainingData` / training-data aspects
   (URN-direct aspect reads or SDK — not search-after-write).
2. For each model, read `MLModelProperties.deployments`.
3. For each deployment URN, read `mlModelDeploymentProperties.status`.

Optional: if the [Recall MCP server](https://github.com/Ahmad-Zeid/recall) is
available, call `assess_defect(source, window_start, window_end)` for the same
traversal with policy gating.

### 3. Scope vs naive reachability

Report both:

- **windowed** — deployments of models that trained on the bad window
- **naive** — everything downstream of the source with no time bound

The delta is the claim. Widening the window "to be safe" is not free.

### 4. Write back so the next agent inherits it

- `add_tags` — e.g. `urn:li:tag:recalled` on contaminated models
- `update_description` / description banner on the model
- `save_document` — decision + evidence + window
- Flip affected deployments to `OUT_OF_SERVICE` via the deployment status aspect
  when policy allows (human gate when blast radius is large)

### 5. Recovery

Release only when **both** are true:

1. source readings are nominal again, and
2. a model exists that never trained on the contaminated window

Then clear tags/banners and return deployments to `IN_SERVICE`.

## Pitfalls

- Empty `get_lineage` on a model ≠ all-clear (see gap above).
- Verify write-back URN-direct — search index lags after writes.
- Already-stopped deployments should be skipped on re-run.
- Do not let the LLM decide the blast radius; use deterministic traversal over
  stored aspects, and keep policy limits outside the model.

## Related

- Full repro + measurements: https://github.com/Ahmad-Zeid/recall/blob/main/docs/upstream-finding.md
- Upstream issue: https://github.com/datahub-project/datahub/issues/19061
- Reference implementation: https://github.com/Ahmad-Zeid/recall
