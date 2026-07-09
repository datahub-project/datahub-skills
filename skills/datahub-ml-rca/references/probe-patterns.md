# Probe patterns: compiling governance metadata into SQL checks

Every probe is SELECT-only, and every probe records which piece of metadata
justified it — the investigation stays explainable end to end.

## Finding the breadcrumbs

Hydrate each upstream dataset's metadata:

```bash
datahub graphql --query '{ dataset(urn: "<DATASET_URN>") {
  tags { tags { tag { properties { name } } } }
  glossaryTerms { terms { term { properties { name definition } } } }
  schemaMetadata { fields { fieldPath nativeDataType description } }
  editableSchemaMetadata { editableSchemaFieldInfo { fieldPath description
    glossaryTerms { terms { term { properties { name definition } } } } } }
} }'
```

Check **both** `schemaMetadata` and `editableSchemaMetadata` — UI-applied
descriptions and terms land on the editable side. Glossary terms often attach
at the **dataset level** with names matching a column (e.g. a "Billing
Amount" term describing `billing_amount`): match terms to columns by
normalized name.

## Compilation table

| Breadcrumb                                                          | Probe (adapt table/column)                                                              | Signal when                          |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------ |
| Event-time column exists (name contains `date`/`time`/`_at`)        | `SELECT MAX(<col>) FROM <table>`                                                        | Falls behind upstream neighbor's max |
| Cadence tag (`daily_refresh`) / SLA glossary term                   | Same as above; the tag tells you the expected period length                             | Lag exceeds ~1 period                |
| Constraint prose: "must/always be positive", "negative … indicates" | `SELECT COUNT(*) FROM <table> WHERE CAST(<col> AS REAL) < 0`                            | Count > 0                            |
| Constraint prose: "never null", "required"                          | `SELECT 100.0 * SUM(CASE WHEN <col> IS NULL THEN 1 ELSE 0 END) / COUNT(*) FROM <table>` | Rate ≥ ~0.5%                         |
| Quality tag (`quality_monitored`, `critical`)                       | NULL-rate scan across text columns                                                      | Rate ≥ ~0.5%                         |
| Event-time column (volume)                                          | `SELECT DATE(<col>), COUNT(*) FROM <table> GROUP BY 1 ORDER BY 1 DESC LIMIT 14`         | Interior hole (see below)            |

## Interpretation rules (these prevent false positives)

1. **Stage-lag beats wall-clock.** Historical or batch datasets are always
   "old"; what matters is a table whose event-time max fell behind its
   _upstream neighbor's_. A stalled load shows up as: upstream max
   `2016-03-10`, downstream max `2016-03-01` — while both tables' ingestion
   metadata says "fresh today".
2. **Volume anomalies are interior holes.** A near-empty period _between two
   healthy periods_ means the pipeline ran and loaded nothing. Near-empty
   periods at the edges of the window are ingestion/sample boundaries —
   ignore them (a trailing stall is the freshness probe's job). Skip volume
   checks entirely on aggregated tables (~1 row per period is their normal).
3. **Constraints inherit across lineage.** Teams document the governed mart,
   not the staging tables. Apply a documented column constraint to every
   lineage node carrying that same column — that is how you show
   contamination flowing from raw intake all the way into a model's feature
   table.
4. **Compare, then conclude.** One probe result is a fact; a diagnosis needs
   the topology (which neighbor is healthy) plus the fact. Keep the two
   separate in your notes.
