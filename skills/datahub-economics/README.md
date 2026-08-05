# DataHub Economics

Price the catalog. Work out what each asset costs, what it costs when it breaks, and write both numbers back into DataHub as structured properties.

## What it does

**Pricing mode:** Attach an annual cost and a value-at-risk to assets, from aspects DataHub already has.

**Decision mode:** Turn those numbers into a defensible action — deprecate, right-size the schedule, protect, or refuse to judge.

1. Establishes a rate card (never invents a price)
2. Reads storage, read, and rebuild signals — `datasetProfile`, `datasetUsageStatistics`, `operation`
3. Propagates consequence upstream from terminal consumers, deduplicating terminals
4. Reaches a deterministic verdict with counter-evidence attached
5. Writes the economics back as structured properties, then verifies with a separate read

## Usage

```
/datahub-economics what does the orders_daily table cost us?
/datahub-economics find deprecation candidates in Snowflake
/datahub-economics what is exposed if the revenue pipeline fails tonight?
/datahub-economics which assets are rebuilt more often than they are read?
```

Or ask naturally: "can we delete this table?", "why is our warehouse bill so high?".

Works on DataHub Core — `usageFeatures`, `storageFeatures`, and `lineageFeatures` are Cloud-only and are deliberately not used. To deprecate an asset once the economics justify it, use `/datahub-enrich`.
