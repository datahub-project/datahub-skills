# DataHub Contract Author

Generate a native DataHub `dataContract` for a dataset from its live metadata and profiling statistics — schema, freshness, volume, and column checks, bound together and emitted through the native declarative path.

## What it does

1. Resolves the dataset and reads its live schema
2. Reads profiling statistics (`datasetProfiles`) to derive evidence-based thresholds
3. Drafts a declarative contract YAML (schema + freshness + volume + column checks)
4. Reviews the plan with the user and gets approval
5. Emits via `datahub.api.entities.datacontract` and verifies the assertions bound

## Capabilities

- **Schema assertion** from the dataset's live `schemaMetadata`
- **Freshness assertion** on a cron or fixed-interval cadence
- **Volume assertion** as a `SELECT COUNT(*)` band derived from the profiled row count
- **Column checks** — not-null and uniqueness derived from field profiles
- **Native path** — the declarative `DataContract` entity API, not the deprecated `datahub datacontract` CLI

## Usage

```
> Give the purchases table a data contract
> Author a data contract for analytics.orders from its profile
> /catalog-contract generate a contract for the trips dataset
```

## Files

| File                                    | Purpose                                                                |
| --------------------------------------- | ---------------------------------------------------------------------- |
| `SKILL.md`                              | Main skill instructions                                                |
| `commands/contract-author.md`           | One-shot "give this dataset a contract" command                        |
| `references/contract-yaml-reference.md` | Full declarative schema: schema / freshness / data_quality / operators |
| `references/profiling-to-assertions.md` | Deriving thresholds from `datasetProfiles`                             |
| `templates/data-contract.template.yml`  | Starter contract YAML                                                  |
| `evaluations/*.json`                    | Behavioral test scenarios                                              |
