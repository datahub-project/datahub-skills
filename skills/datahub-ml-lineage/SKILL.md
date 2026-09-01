---
name: datahub-ml-lineage
description: |
  Use this skill when a lineage question crosses from datasets into ML entities — mlFeature, mlFeatureTable, mlModel, mlModelDeployment. Triggers on: "what data feeds this model", "which columns train X", "does this feature leak the label", "do the offline and online definitions of this feature agree", "what models break if I change this column", "is this model trained on PII", or any request that ends at a model, a feature or an endpoint rather than at a table. For lineage that stays between datasets, dashboards and charts, use `/datahub-lineage`. For ad-hoc catalog questions, use `/datahub-search`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub ML Lineage

`/datahub-lineage` traverses datasets, dashboards and charts. It stops at the warehouse
boundary, so an agent asked "what data actually feeds this model?" tends to stop at the
feature table and guess the rest.

This skill teaches the traversal past that boundary, and — more importantly — the two places
it goes wrong.

## Not This Skill

- Lineage between datasets, dashboards and charts, with no ML entity involved →
  `/datahub-lineage`.
- "Who owns X", "what tables contain PII", one-off catalog lookups → `/datahub-search`.
- Writing owners, terms or documentation onto entities → `/datahub-enrich`.
- Assertion and data-quality state → `/datahub-quality`.

The boundary that matters: those skills answer questions _about the warehouse_. This one
answers questions whose subject is a **model, a feature or an endpoint**, where the warehouse
is only the first half of the path.

## The chain

ML lineage in DataHub is four links, and only the first is ordinary table lineage:

```
Dataset.column ──FineGrainedLineage──▶ Dataset.column   (column-level, inside the warehouse)
Dataset ────────MLFeatureProperties.sources───────────▶ MLFeature
MLFeature ──────MLFeatureTableProperties.mlFeatures───▶ MLFeatureTable
MLFeature ──────MLModelProperties.mlFeatures──────────▶ MLModel
MLModel ────────MLModelProperties.deployments─────────▶ MLModelDeployment
MLModel ────────MLModelProperties.trainingJobs────────▶ DataJob
```

## Trap 1: the granularity break

**`MLFeatureProperties.sources` points at datasets, not columns.**

`FineGrainedLineage` gives you column-level precision inside the warehouse, and then you
cross into ML entities and lose it. An agent that keeps reasoning at column level past that
boundary is inventing precision the graph does not have.

When you need to know _which column_ a feature came from, resolve it explicitly and say how
confident you are:

1. **Declared** — the feature's `customProperties` name their source columns. Trust it.
2. **Name match** — a column in one of `sources` shares the feature's name. This is how
   feature stores that materialise from a table behave, so it is usually right.
3. **Dataset-wide** — no column-level signal. The feature depends on _some_ column of those
   datasets. Report the conclusion as dataset-level, and do not claim otherwise.

Never silently pick one column out of a source dataset because it looks plausible.

## Trap 2: features are not their names

The same logical feature usually exists twice — once offline for training, once online for
serving — as two distinct `MLFeature` entities in two different feature tables. They are
_supposed_ to be identical. Whether they actually are is exactly what nobody checks.

When comparing two paths, compare the **transformations**, not the node names. The offline
and online copies necessarily live in different tables, so any comparison that includes node
identity reports every feature as divergent. Compare the ordered chain of transform
operations, and ignore value-preserving hops (`identity`, `passthrough`) — one path routing
through an extra staging layer is different plumbing, not a different value.

## Workflows

### "What data feeds this model?"

1. `get_entities` on the model URN → read `mlFeatures`.
2. `get_entities` on each feature → read `sources`.
3. `get_lineage` upstream from each source dataset, `direction=UPSTREAM`.
4. For column precision, `get_lineage_paths_between` a candidate source column and the
   feature's dataset — and apply the tiered resolution above before naming columns.

State the deployment status. "Feeds a model" and "feeds a model serving live traffic" are
different answers to the same question.

### "What breaks if I change this column?"

1. `get_lineage` downstream from the column.
2. Filter the result to `mlFeature` and `mlModel` entities — those are the consumers that
   will not raise an error when they break.
3. For each model reached, check `deployments`.

A column change that reaches a deployed model is not a schema question, it is an incident.

### "Does this feature leak the label?"

1. Identify the target column: a `Label` glossary term, or a custom property on the model
   naming it. If neither exists, **say you cannot determine the label** — do not infer it
   from a column called `churned`, `target` or `y`.
2. `get_lineage_paths_between(label_column, feature)`.
3. A path means the feature is derived from the answer. Report the path itself; it is the
   evidence, and it is what makes the finding actionable rather than an accusation.

### "Do offline and online agree?"

1. Find both `MLFeature` entities for the logical feature.
2. Walk each back to shared source columns.
3. Compare transform chains from a shared source, normalised as described in Trap 2.
4. Report the first hop where they differ. That is the line of code to fix.

## Reporting

- Lead with the model and whether it is deployed.
- Show the path. A lineage claim without its path is an assertion; with it, it is evidence.
- Name the confidence tier whenever the answer crossed the granularity break.
- If the graph lacks the ML entities entirely, say so — an instance with no `mlModel`
  entities cannot answer these questions, and that is worth reporting plainly rather than
  approximating from table lineage.

## Contributing back

When you establish something durable — that a feature leaks, that two paths diverged, that a
model depends on restricted data — write it back with `add_tags`, `add_structured_properties`
or `update_description`, so the next agent inherits the conclusion instead of re-deriving it.

---

Extracted from [Faultline](https://github.com/madhavvan/faultline), which uses these
traversals to prove structural ML defects from the DataHub graph. Apache-2.0.
