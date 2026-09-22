# DataHub PR Validation

Validate code changes against DataHub lineage before merging. Detect downstream impact, broken schemas, affected dashboards, and pipeline dependencies.

## What it does

1. Understands what changed (schema, logic, new/removed entity)
2. Traces downstream lineage to find all affected entities
3. Enriches results with ownership for notification
4. Classifies risk level and generates a validation report
5. Suggests next steps and migration actions

## Capabilities

- **Schema change impact** — What breaks if I rename/remove a column?
- **Downstream dependency check** — Who uses this table?
- **Owner notification list** — Who do I need to tell?
- **Risk classification** — How dangerous is this change?
- **Pre-merge validation** — Should I merge this PR?

## Usage

```
/datahub-pr-validation validate PR for stg_orders schema change
/datahub-pr-validation what will break if I rename customer_id in fct_orders
/datahub-pr-validation check dependencies before merging dbt model changes
/datahub-pr-validation impact of removing deprecated_orders column
/datahub-pr-validation validate changes to daily_revenue pipeline
```
