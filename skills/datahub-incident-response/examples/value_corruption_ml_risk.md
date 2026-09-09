# Example: value corruption → ML deployment hold

**Scenario:** `value_corruption` — corrupted `order_items.line_total` values skew
`mart_demand_features.next_day_qty`, threatening `kavach.demand_forecast.prod`.

## Trigger

Sentinel detects custom assertion failure on `raw.order_items` (negative / 100× outliers).

## DataHub workflow

1. **Lineage:** Walk upstream from `main_marts.mart_demand_features.next_day_qty` to
   `raw.order_items.line_total`.
2. **Blast radius:** Downstream includes `kavach.demand_forecast` → prod deployment.
3. **ML Guardian:** Recommend **hold** on deployment (critical severity).
4. **Fix:** Clean outliers in `stg_order_items`; add range assertion.
5. **Write-back:** Create incident, save postmortem Context Document, emit assertion, resolve.

## Artifacts in this repo

| Artifact | Path |
|----------|------|
| Generated Fixer PR | [`examples/prs/value_corruption/`](../../examples/prs/value_corruption/) |
| PR body (DataHub incident URN) | [`examples/prs/value_corruption/pr_body.md`](../../examples/prs/value_corruption/pr_body.md) |
| Chaos scenario definition | [`backend/app/chaos/scenarios/value_corruption.py`](../../backend/app/chaos/scenarios/value_corruption.py) |

## Expected outcome

- Root cause: corrupted line totals skewing demand features.
- ML deployment hold recommended until PR merges.
- Postmortem and tags written to DataHub (see `data/fixtures/writeback.jsonl` for offline trace).
