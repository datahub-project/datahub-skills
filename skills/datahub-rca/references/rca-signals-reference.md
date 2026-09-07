# RCA Signals Reference

Signals used to rank upstream candidates during root-cause analysis, and how to
detect each one from DataHub metadata.

## Freshness lag (weight: high)

The dataset has not been updated within its expected SLA.

- **Detect:** compare the dataset's last-updated / freshness timestamp against
  its expected freshness (from assertions, `get_dataset_assertions` of type
  `FRESHNESS`, or documented SLA).
- **Why it matters:** a stalled ingestion or scheduled job is the single most
  common origin of downstream "wrong numbers" and volume drops.

## Volume anomaly (weight: medium)

The row count deviates sharply (≥ 20%) from its recent baseline.

- **Detect:** `get_dataset_assertions` of type `VOLUME`, or profiling stats.
- **Why it matters:** distinguishes "data stopped flowing" (−100%) from
  "duplicate load" (large positive delta).

## Schema change (weight: high)

Columns were added, removed, or retyped recently.

- **Detect:** `list_schema_fields` + schema history; a `DATA_SCHEMA` assertion
  failure.
- **Why it matters:** a renamed/dropped column silently breaks downstream
  transforms and BI queries.

## Recent query change (weight: medium)

The transform that defines the dataset changed recently.

- **Detect:** `get_dataset_queries` — inspect the defining `CREATE/INSERT`
  statement and its last-modified time.
- **Why it matters:** a modified filter/join/grain changes results without any
  freshness or volume symptom.

## Ranking heuristic

Score = Σ(signal weights) + small bonus for upstream distance.

The origin of a fault is usually the node **furthest upstream** that still
carries a strong signal. Intermediate nodes inherit the symptom but are not the
cause — prefer the origin when signals are comparable.
