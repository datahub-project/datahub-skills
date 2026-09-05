# DataHub ML Leakage

Check whether an ML model's features trace back through DataHub column-level lineage to columns the model must not see.

## What it does

1. Resolves the `mlModel` and confirms the forbidden-tag policy up front
2. Acquires the provenance subgraph — features, source datasets, `fineGrainedLineages`, and field-level tags
3. Walks it deterministically: cycle-safe, hop-bounded, path-preserving
4. Issues a fail-closed verdict (`blocked` / `approved`) with the evidence path
5. Optionally records the decision back to DataHub, after approval

## Capabilities

- **Target leakage detection** — does any feature reach a `post_outcome` column?
- **Pre-deploy authorization** — a reviewable verdict, not a graph to eyeball
- **Evidence paths** — feature → rename → aggregate → forbidden column, with hop counts
- **Fail-closed handling** — missing or truncated lineage blocks rather than passes
- **Decision write-back** — tag the model, raise an incident, record the audit trail

## Usage

```
/datahub-ml-leakage does churn_model_v2 have target leakage?
/datahub-ml-leakage is this model safe to deploy?
/datahub-ml-leakage trace customer_value_score back to its source columns
/datahub-ml-leakage which column caused the block on churn_model_v2?
```

## Not this skill

Use `/datahub-lineage` to explore a graph, `/datahub-enrich` to fix tags, and
`/datahub-quality` for assertions and incident workflows. This skill answers one
question: **is this model allowed to ship, given what feeds it?**
