# DataHub Lifecycle

Retire stale, unused, or superseded assets in DataHub — safely, without breaking the people
still downstream.

## What it does

1. Finds retirement candidates (no usage, no consumers, superseded, or ungoverned)
2. Checks the blast radius first — who still consumes it (lineage) and whether it is still
   queried (usage)
3. Decides: dead → deprecate now; superseded → deprecate with a migration list; still live →
   do not touch, report the dependency
4. Deprecates + notifies: native deprecation flag, a sunset banner, an owner, and a decision
   document
5. Tracks the migration until the asset is finally safe to remove

## Capabilities

- **Stale-asset discovery** — surface tables/dashboards nobody uses
- **Safe deprecation** — gated on downstream consumers and recent queries
- **Sunset records** — reason, replacement, consumers to migrate, decommission date
- **Migration tracking** — the work list to fully retire a superseded asset

## Usage

```
/datahub-lifecycle is it safe to deprecate the legacy_orders table?
/datahub-lifecycle find stale tables nobody queries anymore
/datahub-lifecycle sunset the old_revenue_dashboard and point people to the new one
/datahub-lifecycle what still depends on customers_v1 before I retire it?
```
