# DataHub Enrich

Add and update metadata in DataHub — descriptions, tags, glossary terms, ownership, and deprecation.

## What it does

1. Understands your enrichment intent
2. Resolves target entities and shows current state
3. Builds an enrichment plan with before/after comparison
4. Gets your approval before making any changes
5. Executes updates and verifies they took effect

## Usage

```
/datahub-enrich add tag "important" to customer_orders table
/datahub-enrich set description for revenue_daily
/datahub-enrich assign jdoe as technical owner of analytics tables
/datahub-enrich deprecate legacy_pipeline with note "Replaced by v2"
```

All changes require your explicit approval before execution.

This skill also handles governance metadata operations such as PII tagging, domain assignment, and data products.
