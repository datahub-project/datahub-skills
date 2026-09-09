# DataHub Impact (`datahub-impact`)

Analyze schema change blast radius, calculate multi-factor severity scores, generate remediation migration checklists, and write impact markers back into DataHub.

## What it does

1. **Resolves Target Entity & Schema** — Validates column existence and entity URNs
2. **Traces Combined Lineage** — Pairs column-level lineage with dataset-level lineage to capture pipelines, dashboards, ML models, and jobs
3. **Labels Lineage Confidence** — Distinguishes column-level confirmed impact from dataset-level inferred impact
4. **Ranks Asset Severity** — Applies a 5-factor heuristic (entity type, depth, SQL usage, ownership, environment)
5. **Generates Remediation Plans** — Produces change-type-specific transition checklists (`rename`, `drop`, `type_change`, `add`) grouped by owner
6. **Writes Back to DataHub** — Raises GraphQL incidents on critical assets, sets structured properties, persists markdown report documents, and tags impacted assets

## Usage

```
/catalog-impact rename column customer_id in raw.customers to cust_id
/catalog-impact drop column email in raw.customers
/catalog-impact type change on amount in raw.payments to DECIMAL(18,4)
/catalog-impact add column acquisition_channel to raw.customers
```
