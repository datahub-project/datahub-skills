# DataHub ML Lineage

Audit and protect production ML models using DataHub's end-to-end ML lineage graph (training data → features → models → deployments).

## What it does

1. Resolves the target model and pulls its full upstream lineage in one `get_lineage` call
2. Checks upstream datasets for leakage-signal glossary terms and governance metadata
3. Looks for stale/orphaned upstream tables that a feature's lineage was never repointed to
4. Writes findings back to DataHub (tags, an Analysis document, an updated description) so the next agent or engineer inherits the context
5. Optionally generates the remediation diff against the pipeline code that produced the offending feature

## Capabilities

- **Target leakage detection** — proves a feature is derived from post-outcome data using governance glossary terms, not column-name guessing
- **Blast radius analysis** — finds features still depending on an upstream table that's been silently replaced
- **Retrain triggers** — flags a model trained too long ago against data that has since gone stale
- **ML entity gotchas** — documents where `get_lineage` and `get_entities` behave differently for `MLModel`/`MLFeature` entities, so agents don't assume fields that aren't there

## Usage

```
/datahub-ml-lineage audit churn_predictor for leakage risk
/datahub-ml-lineage what breaks if raw_payments changes?
/datahub-ml-lineage does fraud_model need a retrain?
```
