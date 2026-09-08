# DataHub ML Lineage

Trace ML models through the catalog — features, training data, training runs, deployments — and follow a feature's source dataset down into column-level lineage.

## What it does

1. Identifies the model
2. Reads `mlModelProperties`, which carries most of the chain in one call
3. Walks out to features, feature tables, training datasets, the training run, and deployments
4. Drops into dataset lineage when a question needs column-level detail

## Capabilities

- **Provenance** — What data trained this model?
- **Feature tracing** — Which features does it consume, and where do they come from?
- **Run history** — Which run produced it, on which inputs, and when did it finish?
- **Deployment state** — Is this model actually serving?
- **Impact** — Which models read a column I am about to change?

## Usage

```
/datahub-ml-lineage what data trained churn_predictor?
/datahub-ml-lineage which features does the recommender use?
/datahub-ml-lineage where does the total_amount feature come from?
/datahub-ml-lineage is churn_predictor deployed?
/datahub-ml-lineage what models break if I drop dim_customer.status?
```

## Notes

The ML metamodel records feature sources at **dataset** granularity, not column granularity, so feature-to-column questions resolve through dataset lineage rather than through the feature entity. `mlModelDeployment` cannot be searched by entity type and is reachable only from a model. Both are covered in `references/ml-entity-model.md`.
