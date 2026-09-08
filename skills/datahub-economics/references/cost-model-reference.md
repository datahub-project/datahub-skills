# Cost Model Reference

How to turn DataHub aspects into dollars. Every figure is `observed quantity × a rate the user supplied`.

---

## Rate Card Schema

Collect these before pricing anything. Record them verbatim in every output.

| Key                    | Unit                   | Required | Notes                                                      |
| ---------------------- | ---------------------- | -------- | ---------------------------------------------------------- |
| `storage_usd_tb_month` | USD / TB / month       | Yes      | Blended rate across the platform is fine                   |
| `compute_usd_tb`       | USD / TB processed     | Yes      | Applies to both reads and rebuilds unless split below      |
| `rebuild_usd_tb`       | USD / TB processed     | No       | Override when write compute is billed differently          |
| `terminal_usd_day`     | USD / day per terminal | No       | Default value of a dashboard, model, or data product       |
| `source`               | `contract` \| `list`   | Yes      | If `list`, label every derived figure as vendor list price |

**Credit-based warehouses.** If the user prices in credits, ask for `usd_per_credit` and `credits_per_tb`, then derive `compute_usd_tb = usd_per_credit × credits_per_tb`. Show the derivation — a credit rate applied to the wrong unit is off by orders of magnitude and looks plausible either way.

**Missing rates.** Do not substitute a default. Either ask, or use vendor list price with `source: list` and say so wherever the number appears.

---

## Observation Window

Pick one window, use it for every asset in a run, and print it in the report.

- 30 days is the usual default and matches most usage ingestion schedules.
- Anything shorter than the longest rebuild interval you observe will understate cadence.
- Assets whose earliest signal is newer than the window are partial — reduce confidence rather than extrapolating.

Annualize with `× 365 / window_days`, not `× 12`, so short months do not skew comparisons.

---

## The Three Components

### Storage

```text
storage_usd_year = (sizeInBytes / 1e12) × storage_usd_tb_month × 12
```

From `datasetProfile.sizeInBytes`. Use the most recent profile in the window. If no profile exists, storage is **unknown**, not zero.

### Read compute

```text
reads_in_window  = datasetUsageStatistics.totalSqlQueries
bytes_per_read   = sizeInBytes            # full-scan assumption; state it
read_usd_year    = reads_in_window × (bytes_per_read / 1e12) × compute_usd_tb × 365 / window_days
```

The full-scan assumption is deliberately crude and must be declared. Where `fieldCounts[]` is populated, a column-pruned estimate is better: scale `bytes_per_read` by the fraction of columns actually read.

### Rebuild compute

```text
rebuilds_in_window = count of operation entries in the window
cadence_per_day    = rebuilds_in_window / window_days
rebuild_usd_year   = rebuilds_in_window × (sizeInBytes / 1e12) × (rebuild_usd_tb or compute_usd_tb) × 365 / window_days
```

From the `operation` aspect. This is the component nobody attributes, and it is normally the largest by a wide margin. If `operation` is absent, rebuild cost is **unknown** — that alone is enough to make an asset `UNPRICEABLE` for deprecation purposes, because you cannot quote a saving you cannot measure.

### Total and recoverable

```text
annual_cost_usd      = storage_usd_year + read_usd_year + rebuild_usd_year
recoverable_usd_year = storage_usd_year + rebuild_usd_year
```

`recoverable_usd_year` deliberately excludes read compute. Deprecating an asset does not stop the questions people were asking of it; that work moves to another asset. Quoting `annual_cost_usd` as the saving overstates it by the read share every time.

---

## Right-Sizing an Overserved Asset

```text
reads_per_day  = reads_in_window / window_days
target_cadence = max(reads_per_day, 1/7)          # never slower than weekly
saving_usd_year = rebuild_usd_year × (1 − target_cadence / cadence_per_day)
```

The `1/7` floor keeps a rarely-read but still-live asset from being right-sized into staleness. If `target_cadence >= cadence_per_day`, there is no saving — the asset is not overserved.

---

## Consequence Propagation

1. **Identify terminals.** Dashboards, charts, ML models, and data products — nodes with no downstream data consumer.
2. **Seed each terminal** with an observed value: `dashboardUsageStatistics.viewsCount` or `chartUsageStatistics.viewsCount` scaled by `terminal_usd_day`, or a user-supplied per-terminal value.
3. **Traverse downstream** from each asset, collecting reachable terminal URNs **into a set**.
4. **Sum the set**, once per distinct terminal.

```text
value_at_risk_usd_day(asset) = Σ over distinct reachable terminal URNs of terminal_usd_day
```

Assumptions to declare with the result: hard dependency, no distance decay, terminals deduplicated.

**Why the set matters.** In a diamond (`A → B`, `A → C`, `B → D`, `C → D`), path summation counts dashboard `D` twice for `A`. Real estates are full of diamonds, so the inflation compounds with depth and is not a small error.

**Capped traversals.** If lineage returns a capped or truncated graph, the terminal set is incomplete. Report the value as a lower bound and drop confidence — never present a truncated traversal as a complete one.

---

## Confidence

```text
confidence = (signals present and inside the window) / (signals required for this verdict)
```

| Signal                       | Required for                                   |
| ---------------------------- | ---------------------------------------------- |
| `datasetProfile`             | Any cost figure                                |
| `operation`                  | Any deprecation or right-sizing recommendation |
| `datasetUsageStatistics`     | Any use or disuse claim                        |
| Lineage traversal (uncapped) | Any value-at-risk figure                       |

Report confidence alongside every verdict, and say what would raise it — usually a specific ingestion source that is not enabled. A user who knows which aspect is missing can fix it; a user handed a low number with no explanation cannot.
