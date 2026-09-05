# DataHub Blast Radius

Assess a pending schema change before it ships: what breaks if this column changes, and who
needs to know.

## What it does

1. Resolves the model being changed and pulls its owners, tags, and schema
2. Establishes the full downstream set — as a denominator, not as the answer
3. Queries lineage **per changed column** to find the assets that actually consume it
4. Carries impact one hop further onto the charts and dashboards drawn from affected tables
5. Rates the change from facts a practitioner acts on, with a stated reason for each point
6. Reports the decision first, with the denominator visible

## Capabilities

- Distinguishes drops, renames, and retypes — they carry different risk and different fixes
- Surfaces PII and governance tags on the change path
- Names charts and dashboards, which fail silently rather than erroring
- Flags affected assets that have no owner in DataHub
- Grounds any suggested migration in the consumer's real SQL, never in the column name alone

## Why per-column matters

A wide table can have twenty-five downstream assets while a given column feeds fifteen of
them. Reporting all twenty-five for every change trains people to skip the report. Naming
the four that are provably unaffected is what makes the rest credible.

## When to use something else

| You want to…                         | Use                |
| ------------------------------------ | ------------------ |
| Explore lineage or find a root cause | `/datahub-lineage` |
| Ask who owns or documents an asset   | `/datahub-search`  |
| Apply tags, owners, or descriptions  | `/datahub-enrich`  |
| Manage assertions and incidents      | `/datahub-quality` |
