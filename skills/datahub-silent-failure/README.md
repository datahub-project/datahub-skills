# DataHub Silent Failure Root-Cause

Root-cause a **silent failure** — a downstream asset that degraded even though
nothing errored — by walking lineage upstream, checking freshness at every hop in
the data plane, and installing a guard on the table that actually broke.

## The problem

A model's accuracy drifts. A dashboard's numbers go wrong. No job failed, no
alert fired, every dashboard is green.

Somewhere upstream, a table stopped receiving data. Everything downstream kept
serving the last data it had — confidently, and without complaint. A stalled load
does not raise an error; it just stops.

## Why a separate skill

Two existing skills each hold half the answer:

- `datahub-lineage` can tell you **where to look**.
- `datahub-quality` can tell you **what to install afterwards**.

Neither, on its own, tells you **which upstream table actually broke** — and the
step that joins them has a trap in it (below).

## The trap

**Ingestion metadata cannot see a stalled load.** DataHub records that the
_ingestion_ ran, not that the _data_ arrived. If an upstream job stops writing
rows while your ingestion keeps running on schedule, every table reports the same
healthy "last ingested" timestamp — including the one that has been frozen for
three days.

Freshness truth lives in the data plane. You have to query the warehouse:

```sql
SELECT MAX(<date_column>) FROM <table>;
```

Metadata says healthy; the data says stale. **That gap is the silent failure** —
and it is invisible from the catalog alone.

## What the skill does

1. Establishes the affected asset and the date the degradation appeared.
2. Walks lineage upstream — reading the path from the graph, not assuming it
   (for ML models, through `mlFeature`, not dataset lineage).
3. Probes freshness at **every** dataset hop, in the data plane.
4. Names the culprit: the **first** stale hop, whose own upstream is fresh.
   Everything below it is a symptom.
5. Or exonerates the pipeline — if every hop is fresh, the data arrived on time
   and is simply unusual (a storm, a holiday, a demand shock). Saying so is as
   important as finding a culprit; a false "the pipeline broke" sends an engineer
   to fix a healthy system.
6. Installs a freshness guard on the culprit, so the next occurrence is caught at
   the source, on the first missed load.

## Usage

```text
/datahub-silent-failure my fare model's error jumped on 2026-07-09 but nothing errored
/datahub-silent-failure why is the revenue dashboard stale when the job succeeded?
```

## Files

| File                                      | Purpose                                              |
| ----------------------------------------- | ---------------------------------------------------- |
| `SKILL.md`                                | The workflow                                         |
| `references/freshness-guard-reference.md` | Guard mutations for OSS and Cloud, and their gotchas |
