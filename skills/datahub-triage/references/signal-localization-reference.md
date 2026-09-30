# Signal localization reference

How to turn per-stage health signals into a root-cause verdict.

## The boundary rule

Walk the lineage from the symptom (hop 0) toward the sources. A stage is either
**healthy** or **unhealthy** for the symptom's signal. The root cause is the boundary:

```
healthy source → ... → healthy stage → UNHEALTHY stage → ... → unhealthy symptom
                                        ^^^^^^^^^^^^^^^^
                                        root cause (break originates here)
```

Everything downstream of the break is **carrying** the problem (propagation).
Everything upstream is fine. The single unhealthy-meets-healthy boundary is the origin.

## Per-symptom signals

| Symptom       | Per-stage signal                                                                          | "Unhealthy" means                                           | Root cause is...                         |
| ------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------- |
| `FRESHNESS`   | latest update time (`operations`, `lastModified`, or a `FIELD_VALUE` freshness assertion) | this stage's data time lags its upstream beyond the cadence | first stage that lags its upstream       |
| `VOLUME`      | row count (`latestAssertionStatusByType`, volume assertion)                               | row count dropped versus upstream / history                 | first stage where the drop appears       |
| `FIELD`       | failing field assertion count for the column                                              | the failing check is present in this stage's data           | deepest upstream stage that still fails  |
| `DATA_SCHEMA` | schema version / schema assertion                                                         | the schema change first appears here                        | stage where the column was added/removed |
| `OPERATIONAL` | active incidents, failed operation status                                                 | active incident or failed run whose upstream is clean       | most upstream stage with the failure     |

## Freshness vs. quality: opposite directions

- **Freshness** localizes to the **first lagging stage** going up — a middle stage that
  stopped pulling. The source is usually fine.
- **Quality** localizes to the **deepest failing stage** — defects propagate unchanged,
  so if raw, staging, and mart all fail the same check, the origin is raw.

Do not mix these up. A stale mart with a fresh source points to a broken middle stage;
a mart full of nulls that trace all the way to raw points to raw.

## Forks (one stage feeding several downstreams)

A staging table often forks into multiple marts. A defect in staging reaches every
downstream, but each downstream is affected **differently** — a `billing` mart cares
about negative amounts; a `demographics` mart cares about invalid ages.

Triage **selectively**: only consider signals that actually reach the symptom you were
called about. A billing symptom should not be blamed on an age defect that forked to a
different mart, even though both share the same upstream. Check which failing signal is
present on the symptom asset itself, then trace **that** signal upstream.

## Siblings (dbt vs. warehouse)

Lineage may return a dbt model URN when the user is thinking of the warehouse table (or
vice versa) — they are linked via the `siblings` aspect. Treat a stage and its sibling
as one logical stage when localizing; note the sibling platform in the report so the
owner knows where to fix it (the dbt model, not the materialized table).

## Confidence

- **High:** a single clean boundary — one stage unhealthy, its upstream healthy, the
  signal is unambiguous (e.g. a 9-day freshness gap).
- **Medium:** the boundary is fuzzy (small lag, or several stages marginally off).
- **Low / needs data check:** metadata is clean but the symptom is real — you are
  inferring from the data-level fallback, not catalog signals. Say so.
