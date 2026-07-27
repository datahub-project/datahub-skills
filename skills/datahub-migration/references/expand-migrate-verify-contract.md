# Expand -> Migrate -> Verify -> Contract

The four-phase pattern this skill executes, and why each phase exists.

## Expand

Add the new column/field alongside the old one -- additive DDL only,
backfilled from the old value. The old column is never touched. This
phase is reversible by construction: if anything downstream goes wrong,
there is nothing to roll back on the source table itself.

## Migrate

One code change per consumer that has a real reference to rewrite,
sequenced by topological distance from the target so a consumer never
migrates before its own upstream. Not every consumer in the blast radius
needs a diff here -- a consumer that only reads an already-derived,
aliased value (e.g. `sum(order_total) as lifetime_value`) inherits the
fix for free once its upstream is migrated, because its own output name
never changes.

**Renames must propagate consistently.** If a bare (unaliased)
projection is renamed at one layer, every consumer of that layer must
also rename its own reference to match -- aliasing the renamed column
back to its old name at just one layer to "preserve the contract" is
inconsistent once other layers in the same batch are also being
rewritten, and produces code that references a column name that will
never actually exist.

## Verify

Prove correctness before committing to the change for real -- not after.
The hard part: a downstream consumer's rewritten SQL references its
immediate parent's *new* column, but that parent isn't actually
redeployed yet at verification time. Rather than staging a real deploy
at every hop just to prove one query, chain every migrated ancestor's own
old/new SQL together (as CTEs) into one self-contained query per
consumer. Virtually expand the root source table inside the query itself
(a `CAST`) until the real expand DDL has actually run, then compare row
counts and value equality between the old and new chains on a real key
column.

## Contract

Only after every consumer in the plan has a passing verification:
deprecate the old column with a sunset date and a replacement pointer,
and write a migration playbook back onto the target entity. "Contract"
here means catalog-level deprecation with a grace period, not an
immediate physical drop of the old column -- that's a separate, later,
deliberately irreversible action that happens well after the sunset date
passes, not as part of this run.

## The two-stage lineage gap

DataHub's fine-grained (per-column) lineage only exists on dataset-to-
dataset `upstreamLineage` edges. Charts, dashboards, and ML feature
tables express their own upstream via table-level fields
(`ChartInfo.inputs`, `MLFeatureProperties.sources`), because that's what
real BI tools and feature stores actually report -- most don't track
column-level provenance at all. A column-scoped lineage traversal will
correctly find every dataset consumer, but will never surface these
entities, even though they are genuinely downstream. Catching them
requires a second, unscoped, table-level hop from each dataset found in
the first pass.
