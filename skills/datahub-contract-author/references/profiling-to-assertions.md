# Profiling to Assertions Reference

How to turn a dataset's profiling statistics into evidence-based contract checks. The goal is that every threshold in the contract traces back to a measured value — never a guess.

## Reading the profile

`datasetProfile` is a **timeseries** aspect. Read the latest one via GraphQL (not `datahub get`, which reads versioned aspects only):

```graphql
query ($urn: String!) {
  dataset(urn: $urn) {
    datasetProfiles(limit: 1) {
      rowCount
      columnCount
      fieldProfiles {
        fieldPath
        nullCount
        nullProportion
        uniqueCount
        uniqueProportion
        min
        max
      }
    }
  }
}
```

If `datasetProfiles` is empty, the dataset has not been profiled. Do not invent thresholds — propose a schema + freshness contract only, or ask the user for expected bounds.

## The mapping

| Profile signal                   | Contract check                                                                                         | Notes                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| `rowCount`                       | Volume: `custom_sql` `SELECT COUNT(*) FROM <table>` with `between { min, max }`                        | Pick a band around the observed count (see below).             |
| Field `nullProportion == 0`      | Not-null: `custom_sql` `SELECT COUNT(*) FROM <table> WHERE <col> IS NULL` with `equal_to { value: 0 }` | Only for columns observed to be fully populated.               |
| Field `uniqueProportion == 1.0`  | Uniqueness: `type: unique` on the column                                                               | Typical for ids and natural keys.                              |
| Field `min` / `max`              | Range: `custom_sql` `SELECT COUNT(*) ... WHERE <col> < min OR <col> > max` with `equal_to 0`           | Use with care — real ranges drift; widen the observed band.    |
| The live `schemaMetadata` fields | Schema block (`json-schema` or `field-list`)                                                           | Mark columns the profile shows always-populated as `required`. |

## Choosing a volume band

The right band depends on how the table grows:

- **Stable / slowly changing dimension:** `between` the observed count ±10–20%. Example: `rowCount = 145,280` → `min: 130,000, max: 160,000`.
- **Append-only / growing fact table:** a floor makes more sense than a band — `greater_than_or_equal_to { value: <observed count> }` — so the check does not fail simply because the table grew.
- **Partitioned / daily load:** band the expected per-load count, not the lifetime total, and scope the SQL to the partition.

State the reasoning to the user and let them adjust. The band is a starting point derived from one profile snapshot, not a guarantee.

## Worked example

Profile:

```json
{
  "rowCount": 145280,
  "columnCount": 2,
  "fieldProfiles": [
    {
      "fieldPath": "id",
      "nullProportion": 0.0,
      "uniqueProportion": 1.0,
      "min": "1",
      "max": "145280"
    },
    { "fieldPath": "email", "nullProportion": 0.0, "uniqueProportion": 1.0 }
  ]
}
```

Derived `data_quality`:

```yaml
data_quality:
  - type: custom_sql
    description: row count within observed band
    sql: "SELECT COUNT(*) FROM analytics.purchases"
    operator: { type: between, min: 130000, max: 160000 }
  - type: custom_sql
    description: id is never null
    sql: "SELECT COUNT(*) FROM analytics.purchases WHERE id IS NULL"
    operator: { type: equal_to, value: 0 }
  - type: unique
    column: id
  - type: custom_sql
    description: email is never null
    sql: "SELECT COUNT(*) FROM analytics.purchases WHERE email IS NULL"
    operator: { type: equal_to, value: 0 }
```

Every threshold above is traceable to a profiled value.
