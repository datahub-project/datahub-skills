# Example: freshness lag on orders ingestion

**Scenario:** `freshness_lag` — stale `raw.orders` partition causes downstream revenue mart
and demand features to lag beyond SLA.

## DataHub workflow

1. **Detect:** Freshness assertion failure on `raw.orders`.
2. **Root-cause:** Ingestion delay; upstream source freshness metadata stale.
3. **Blast radius:** `mart_daily_revenue`, `mart_demand_features`, linked dashboards.
4. **Fix:** Backfill DAG + widen source freshness window in dbt sources.yml.
5. **Write-back:** Open incident, document backfill steps in Context Document, resolve.

## Artifacts

| Artifact | Path |
|----------|------|
| Fixer PR | [`examples/prs/freshness_lag/`](../../examples/prs/freshness_lag/) |
| Scenario | [`backend/app/chaos/scenarios/freshness_lag.py`](../../backend/app/chaos/scenarios/freshness_lag.py) |
