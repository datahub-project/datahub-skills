# DataHub Migration

Plan and execute a safe, verified column-level schema migration --
retype, rename, or deprecate-and-replace -- using DataHub's lineage as
the source of truth for blast radius.

## What it does

1. Confirms the migration intent (target column, what's changing, sunset
   window)
2. Finds the real blast radius with a two-stage lineage traversal
   (column-level for dataset consumers, table-level fan-out for BI/ML
   consumers that don't report column lineage at all)
3. Sequences an expand -> migrate -> verify -> contract plan
4. Proves every consumer's whole propagated chain correct with a chained
   parallel-run query, before committing to any real change
5. Opens real PRs, re-verifies against the real warehouse, and -- only if
   everything passes -- deprecates the old column and writes a playbook
   back into the catalog

## Capabilities

- **Two-stage blast radius** -- catches BI dashboards and ML feature
  tables that column-level lineage alone would miss
- **Chained verification** -- proves a multi-hop migration correct in
  one query per consumer, without staging a real deploy at every layer
- **Real execution, not a report** -- actual PRs, actual warehouse
  verification, actual catalog write-back
- **Playbook memory** -- every migration leaves a reusable record for
  the next (possibly sibling) migration

## Usage

```
/datahub-migration retype order_total to DECIMAL(12,2) on raw.orders
/datahub-migration deprecate email, move consumers to email_sha256
/datahub-migration what would it take to safely rename customer_id?
```

## Origin

Built for and proven by [RippleX](https://github.com/nnam-droid12/ripplex),
an autonomous data-migration agent built for the Build with DataHub
hackathon. Every technique in this skill -- the two-stage traversal, the
chained parallel-run, the four-phase gate -- was discovered and verified
against a real DataHub instance, a real warehouse, and real PRs, not
designed in the abstract.
