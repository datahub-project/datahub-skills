---
name: datahub-silent-failure
description: |
  Use this skill when a downstream consumer degrades but nothing errored — a model's accuracy drifts, a dashboard's numbers go wrong, a metric moves and no job failed and no alert fired. This is a silent failure: an upstream table stopped receiving data, so everything downstream is serving stale data confidently. This skill walks lineage upstream from the affected asset, checks freshness at every hop, identifies the first stale hop as the culprit, and installs a freshness guard so the same failure is caught at the source next time. Triggers on: "silent failure", "stale data", "nothing errored but", "no alert fired", "model degraded", "numbers look wrong", "why is my dashboard stale", "data is old but the job succeeded", "root cause a data quality issue", or any degradation with no error to point at.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Silent Failure Root-Cause

You are an expert data reliability engineer. Your role is to root-cause a **silent
failure**: a downstream asset that has degraded even though nothing errored.

A silent failure has a specific shape:

- A consumer (an ML model, a dashboard, a report) is producing worse output.
- No job failed. No pipeline errored. No alert fired.
- Somewhere upstream, a table stopped receiving data — and everything downstream
  kept serving the last data it had, confidently and without complaint.

The failure is silent precisely because a stalled load does not raise an error.
It just stops. Downstream consumers cannot tell "yesterday's data" from
"today's data that happens to look like yesterday's".

This skill exists because the two things you need are in different places:
`datahub-lineage` can tell you **where to look**, and `datahub-quality` can tell
you **what to install afterwards** — but neither, on its own, tells you which
upstream table actually broke.

---

## ⚠️ The trap that defines this skill

**Ingestion metadata cannot see a stalled load.**

When you ingest a source, DataHub records that _the ingestion ran_. It does not
record that _the data arrived_. If an upstream ETL job stops writing rows but
your ingestion keeps running on schedule, every table in the catalog reports the
same healthy "last ingested" timestamp — including the table that has been
frozen for three days.

So: **do not diagnose freshness from catalog metadata alone.** Freshness truth
lives in the data plane. You must query the warehouse:

```sql
SELECT MAX(<date_or_timestamp_column>) FROM <table>;
```

The contrast is the diagnosis. Metadata says healthy; the data says stale. That
gap is the silent failure, and it is invisible from the catalog alone.

---

## Multi-Agent Compatibility

Designed to work across coding agents (Claude Code, Cursor, Codex, Copilot,
Gemini CLI, Windsurf, and others).

**What works everywhere:** the full diagnostic workflow (lineage traversal,
freshness probing, root-cause identification) and guard registration via
`datahub graphql`.

**Claude Code-specific:** the `allowed-tools` frontmatter above. Other agents can
ignore it.

---

## Deployment tiers

| Capability                                      | OSS | Cloud |
| ----------------------------------------------- | --- | ----- |
| Lineage traversal to find upstream hops         | ✅  | ✅    |
| Freshness probing in the data plane             | ✅  | ✅    |
| Register an external freshness guard            | ✅  | ✅    |
| Report guard results (pass/fail)                | ✅  | ✅    |
| Native + smart (AI-inferred) assertion monitors | ❌  | ✅    |

On **OSS**, register the guard as an _external_ assertion (`upsertCustomAssertion`)
and report its results yourself (`reportAssertionResult`). You supply the
evaluation. See `references/freshness-guard-reference.md`.

On **Cloud**, prefer a native freshness assertion with a monitor — the platform
schedules and evaluates it for you. See the `datahub-quality` skill.

---

## Step 1: Establish the symptom

Get two things from the user before touching the graph. Ask if not provided:

1. **The affected asset** — the model, dashboard, or dataset that degraded. You
   need its URN. Use the `datahub-search` skill or `search` if you only have a name.
2. **The date the degradation appeared** (the "as-of" date). Everything you
   conclude is relative to this date. Without it you cannot tell a table that is
   stale _now_ from one that was stale _then_.

> If the user reports a _hard_ failure — a job errored, an alert fired, a
> pipeline is red — this is not a silent failure. Use the `datahub-quality`
> skill instead.

---

## Step 2: Walk lineage upstream — do not assume the shape

Traverse upstream from the affected asset. **Read the path from the graph rather
than assuming it.** The chain you expect and the chain that exists are often
different — that is usually the whole reason the failure went unnoticed.

For an ML model, the path runs through the ML entities, **not** through dataset
lineage:

```text
mlModel --Consumes--> mlFeature --DerivedFrom--> dataset --upstream--> dataset
```

Keep walking until you reach root tables (no upstreams).

> **Note:** `upstreamLineage` is not a valid aspect on `mlModel`. ML lineage
> flows through `MLModelProperties.mlFeatures` and `MLFeatureProperties.sources`.
> Traversal via `get_lineage` (MCP) or the `lineage` GraphQL field handles this
> for you — but if you are emitting this lineage yourself, emit those, not a
> dataset lineage edge.

---

## Step 3: Probe freshness at EVERY hop, in the data plane

For every **dataset** on the path (models and features hold no data of their
own), get the latest date actually present in the table, and compare it to the
as-of date from Step 1:

```sql
SELECT MAX(trip_date) FROM staging_trips;
```

Record for each hop: `max_data_date`, `days_behind_as_of`, and
`rows_on_as_of_date`.

Do not stop at the first stale table you find. A stale table whose upstream is
_also_ stale is a symptom, not the cause.

---

## Step 4: Identify the culprit — the FIRST stale hop

Walk the results from the root downward. The culprit is the **furthest-upstream
dataset that is stale while its own upstream is fresh**. That boundary — fresh
above, stale below — is the broken link.

Everything downstream of it is collateral. Reporting a downstream symptom as the
root cause sends someone to fix a table that is working perfectly.

### The other verdict: it may not be a pipeline failure at all

If **every** dataset on the path is fresh as of the date in question, the
pipeline is healthy and **must not be blamed**. The data arrived on time; it is
simply unusual. A storm, a holiday, an outage at the source, a demand shock.

Distinguish them with a volume probe — rows per day across the window:

- **Pipeline failure** → the culprit has _no rows at all_ for the affected days.
- **Failed load** → the day is present but _empty_ (zero rows).
- **Real-world anomaly** → rows are present, just _fewer_, and the dip
  **propagates faithfully** to every downstream table. The pipeline did its job.

Say so plainly when the pipeline is exonerated. A false "the pipeline broke" is
worse than no diagnosis: it sends an engineer to fix a healthy system while the
real cause goes unexamined.

---

## Step 5: Beware of what previous runs wrote

The catalog may already carry tags, descriptions, or assertion results left by a
**previous** incident — possibly one that was long since fixed.

**Those are prior claims, not current facts.** Your own probes are ground truth
for _this_ incident. If an annotation says a table failed but your probe shows it
fresh as of the as-of date, believe the probe, and say so explicitly.

This matters more than it sounds. Agents that write conclusions back into the
catalog also _read_ the catalog — so yesterday's conclusion becomes today's
evidence. An undated "load stalled" note left on a table will happily convince
the next investigation that a perfectly healthy pipeline is broken.

**When you write findings back, date them and attribute them.** Never leave an
undated conclusion behind.

---

## Step 6: Install the guard

The failure went unnoticed because nothing was watching the culprit. Fix that.

Register a freshness assertion on the **culprit** (not on the asset that
degraded — the symptom already has plenty of attention):

- Threshold: the table's expected load interval. A table loaded daily should
  assert freshness every 24h.
- **Use `>=`, not `>`.** A table exactly 24h stale has _already missed_ a daily
  load. A strict `>` sleeps through the first missed day and only wakes on the
  second — forfeiting most of the warning time the guard exists to buy.

Then report a result so the guard is not an empty shell — the failing run is what
makes it visible in the Validation tab. Put the evidence in the result payload
(`hours_since_last_load`, `threshold_hours`) so the red X explains itself.

Full OSS + Cloud mutations: `references/freshness-guard-reference.md`.

---

## Step 7: Report

State, in this order:

1. **The verdict** — `pipeline_failure` or `real_world_anomaly`.
2. **The culprit** (if any) — the URN, and how far behind it is.
3. **The causal chain** — from the degraded asset back to the culprit, hop by hop.
4. **The evidence** — the probe results that decided it, per hop.
5. **The guard** — what you installed, and what it will catch next time.

Write the findings back to DataHub so the next person (or agent) inherits them:
tag the culprit, and attach the incident to the degraded asset. Date every
annotation (see Step 5).

---

## Why this ordering matters

Detection is not the achievement — a badly degraded model gets noticed
eventually, by someone, painfully. The achievement is naming **which** upstream
table broke, and installing a guard that fires at the source on the _first_
missed load, days before the damage reaches the consumer.
