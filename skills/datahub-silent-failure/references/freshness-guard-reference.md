# Freshness Guard Reference

How to install a freshness guard on the culprit table after root-causing a silent
failure, and how to report its results so it renders in the Validation tab.

All OSS examples below were verified against DataHub OSS quickstart `v1.5.0.6`.

---

## OSS: external assertion + self-reported results

On OSS you register an **external** assertion and supply the evaluation yourself.
This is the `upsertCustomAssertion` / `reportAssertionResult` pair already listed
in the `datahub-quality` skill's OSS capability table.

### 1. Register the guard

```graphql
mutation {
  upsertCustomAssertion(
    urn: "urn:li:assertion:my-freshness-guard"
    input: {
      entityUrn: "urn:li:dataset:(urn:li:dataPlatform:sqlite,db.staging_trips,PROD)"
      type: "FRESHNESS"
      description: "staging_trips must receive a load every 24h"
      platform: { urn: "urn:li:dataPlatform:sqlite" }
    }
  ) {
    urn
  }
}
```

### 2. Report a result

```graphql
mutation {
  reportAssertionResult(
    urn: "urn:li:assertion:my-freshness-guard"
    result: {
      timestampMillis: 1770000000000
      type: FAILURE # or SUCCESS
      properties: [
        { key: "hours_since_last_load", value: "72" }
        { key: "threshold_hours", value: "24" }
      ]
    }
  )
}
```

Put the evidence in `properties`. A red X that shows _why_ it is red is worth far
more than one that just says "failed".

### ⚠️ Gotcha: the assertion must be indexed before you can report on it

Calling `reportAssertionResult` immediately after `upsertCustomAssertion` fails
with:

```text
Failed to report Assertion Run Event. Assertion with urn <...> does not exist
or is not associated with any entity.
```

This is **search-index propagation lag, not a real error** — the assertion does
exist. Waiting ~2 seconds between the two calls resolves it. If you are
scripting this, retry the report with a short backoff rather than treating the
first failure as fatal.

---

## OSS: the aspect-level equivalent (Python SDK / MCP)

If you are emitting metadata directly rather than going through GraphQL, the same
guard is an `AssertionInfo` aspect plus `AssertionRunEvent` aspects:

```python
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    AssertionInfoClass, AssertionTypeClass, AssertionSourceClass,
    AssertionSourceTypeClass, FreshnessAssertionInfoClass,
    FreshnessAssertionTypeClass, FreshnessAssertionScheduleClass,
    FreshnessAssertionScheduleTypeClass, FixedIntervalScheduleClass,
    CalendarIntervalClass, AssertionRunEventClass, AssertionResultClass,
    AssertionResultTypeClass, AssertionRunStatusClass)

emitter = DatahubRestEmitter(gms_server="http://localhost:8080")
ASSERTION = "urn:li:assertion:my-freshness-guard"
CULPRIT = "urn:li:dataset:(urn:li:dataPlatform:sqlite,db.staging_trips,PROD)"

emitter.emit(MetadataChangeProposalWrapper(
    entityUrn=ASSERTION,
    aspect=AssertionInfoClass(
        type=AssertionTypeClass.FRESHNESS,
        description="staging_trips must receive a load every 24h",
        source=AssertionSourceClass(type=AssertionSourceTypeClass.EXTERNAL),
        freshnessAssertion=FreshnessAssertionInfoClass(
            type=FreshnessAssertionTypeClass.DATASET_CHANGE,
            entity=CULPRIT,
            schedule=FreshnessAssertionScheduleClass(
                type=FreshnessAssertionScheduleTypeClass.FIXED_INTERVAL,
                fixedInterval=FixedIntervalScheduleClass(
                    unit=CalendarIntervalClass.HOUR, multiple=24),
            ),
        ),
    )))

ts = 1770000000000
emitter.emit(MetadataChangeProposalWrapper(
    entityUrn=ASSERTION,
    aspect=AssertionRunEventClass(
        timestampMillis=ts,
        runId=f"guard-{ts}",
        assertionUrn=ASSERTION,   # required IN ADDITION to entityUrn — easy to miss
        asserteeUrn=CULPRIT,
        status=AssertionRunStatusClass.COMPLETE,
        result=AssertionResultClass(
            type=AssertionResultTypeClass.FAILURE,
            actualAggValue=72.0,
            nativeResults={"hours_since_last_load": "72",
                           "threshold_hours": "24"},
        ),
    )))
```

### ⚠️ Gotcha: `client.assertions.sync_*` does not work on OSS

The `acryl-datahub-cloud` SDK's `client.assertions.sync_freshness_assertion(...)`
fails against an OSS instance with:

```text
Failed to find entity with name monitor in EntityRegistry (HTTP 422)
```

The reason is worth knowing: `sync_*` creates **two** entities — an `assertion`
_and_ a `monitor`. The assertion is part of the OSS metadata model; the `monitor`
(Cloud's scheduling and evaluation engine) is not. So the Cloud SDK is gated by
the monitor, not by the assertion.

Note the failed call still creates the assertion entity before dying on the
monitor, leaving an orphan behind. Clean it up with
`graph.soft_delete_entity(urn)`.

### ⚠️ Gotcha: soft-deleted assertions do not come back on re-emit

Soft-deleting sets `removed=true`. Re-emitting the assertion's aspects does
**not** clear that flag — the assertion stays invisible in the Validation tab.
Emit `StatusClass(removed=False)` to revive it, or hard-delete and recreate.

---

## Cloud: native assertion + monitor

On Cloud, prefer a native freshness assertion with a monitor — the platform
schedules and evaluates it for you, and smart (AI-inferred) monitors need no
threshold at all. See the `datahub-quality` skill:

- `createFreshnessAssertion`
- `upsertDatasetFreshnessAssertionMonitor` (`inferWithAI: true` for smart mode)

---

## Choosing the threshold

Set the threshold to the table's **expected load interval**, and compare with
`>=`, not `>`.

A table loaded daily that is exactly 24h stale has **already missed a load**. A
strict `>` will not fire until hour 25 — so the guard sleeps through the entire
first missed day and only wakes on the second. On a three-day stall, that
forfeits a third of the warning time, which is most of the reason the guard
exists.

| Load cadence | Threshold | Fires when                |
| ------------ | --------- | ------------------------- |
| Hourly       | 1h        | one hourly load is missed |
| Daily        | 24h       | one daily load is missed  |
| Weekly       | 168h      | one weekly load is missed |
