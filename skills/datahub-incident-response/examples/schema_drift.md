# Example: schema drift on supplier feed

**Scenario:** `schema_drift` — supplier feed renamed `quantity` → `qty`, breaking
`stg_order_items` join and spiking nulls on `mart_demand_features.next_day_qty`.

## DataHub workflow

1. **Detect:** Schema assertion / null-rate spike on mart column.
2. **Root-cause:** Upstream lineage shows column rename on `raw.order_items`.
3. **Query history:** Recent transforms reference old column name.
4. **Fix:** Alias `qty AS quantity` in staging model; add schema contract test.
5. **Write-back:** Incident + Context Document + tags.

## Artifacts

| Artifact | Path |
|----------|------|
| Fixer PR | [`examples/prs/schema_drift/`](../../examples/prs/schema_drift/) |
| Scenario | [`backend/app/chaos/scenarios/schema_drift.py`](../../backend/app/chaos/scenarios/schema_drift.py) |
