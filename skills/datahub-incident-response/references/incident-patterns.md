# Incident Evidence Patterns

These patterns help form hypotheses. A pattern match is not proof of causality. Cite the actual
DataHub entity and field, record contradictory evidence, and name the production check that would
confirm or reject the hypothesis.

## Silent Partial Load

- Consumer symptom: a metric drops sharply while orchestration reports success.
- Supporting metadata: a source or boundary entity records a much smaller row count or a note about
  omitted partitions; the magnitude and time align with the consumer symptom.
- Weakening evidence: normal source volume, a mismatch in timing, or an intervening transformation
  that could independently change the measure.
- Confirm next: compare source and target row counts by partition against the recent baseline and
  inspect the source response or ingestion log.

## Schema Drift

- Consumer symptom: one or more fields become null, blank, or semantically wrong.
- Supporting metadata: an upstream field was renamed, removed, or changed type while a downstream
  mapping or transformation still refers to the previous contract.
- Weakening evidence: unchanged schema, a compatible mapping update, or nulls already present at the
  source before the alleged change.
- Confirm next: diff the source schema and transformation at the first failing partition, then test
  a representative record end to end.

## Freshness or No-Op Load

- Consumer symptom: a metric is frozen or lags its expected cadence.
- Supporting metadata: a last-load or freshness field is older than the promised cadence, or a job
  succeeded without producing a new partition.
- Weakening evidence: current source timestamps or a dashboard cache that is older than the dataset.
- Confirm next: compare event time, ingestion time, and dashboard refresh time; inspect the upstream
  feed and most recent produced partition.

## Transformation Regression

- Consumer symptom: totals, joins, or segment membership change after a deployment.
- Supporting metadata: the exact lineage path includes a changed query or model at the matching
  time; upstream inputs remain stable.
- Weakening evidence: unchanged transformation text, a source anomaly of matching magnitude, or an
  unrelated deployment window.
- Confirm next: reproduce the transformation for a bounded partition and compare it with the prior
  version.

## Classification Checklist

For each candidate ask:

1. Does its timing match first observation?
2. Does its magnitude or field-level effect match the symptom?
3. Is it the earliest supported fault location, or merely a downstream carrier?
4. Is the lineage response complete for the claimed boundary?
5. What evidence contradicts the hypothesis?
6. What one check would most cheaply confirm or reject it?

If no candidate survives these checks, report insufficient evidence. Do not choose a root cause
only because an entity name or description sounds suspicious.
