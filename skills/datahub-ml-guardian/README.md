# DataHub ML Guardian

Catch silent upstream data changes that break production ML models — trace the lineage,
score the risk, and write the warning back into DataHub.

## What it does

1. Resolves a changed table/column to its dataset URN
2. Traces downstream ML lineage (`dataset → mlFeature → mlModel → deployment`), column-precise
3. Classifies the risk (silent, no-error changes that reach a prod model = critical) and
   quantifies the damage as a metric delta
4. Remediates with a fail-loud guard + a pull request
5. Writes back to the graph: tags, owner, and an incident document — fully reversible

## Capabilities

- **ML impact analysis** — Which production models break if I change this column?
- **Silent-drift detection** — Unit/semantic drift, renames, type changes that pass CI
- **Precise blast radius** — Flags only the models a change actually reaches
- **Metric quantification** — Reads `trainingMetrics`; reports the AUC/metric delta
- **Write-back** — `add_tags`, `add_owners`, `save_document` (+ SDK deprecation/incident)

## Usage

```
/datahub-ml-guardian is it safe to rename purchase_amount_cents on customer_orders?
/datahub-ml-guardian what production models break if raw_orders changes units?
/datahub-ml-guardian trace this schema change to any ML models and flag the risk
/datahub-ml-guardian a column switched from cents to dollars — assess the ML impact
```
