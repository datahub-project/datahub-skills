# Assertion Mutations Reference

All write operations use `datahub graphql --query '...' --format json`. For dataset URNs (which contain parentheses), use `--variables` with a temp JSON file.

---

## URN Quoting

```bash
cat > /tmp/quality-vars.json << 'EOF'
{ "entityUrn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table,PROD)" }
EOF

datahub -C skill=datahub-quality graphql \
  -q 'mutation run($entityUrn: String!) { runAssertionsForAsset(urn: $entityUrn) { passingCount failingCount } }' \
  -v /tmp/quality-vars.json --format json

rm /tmp/quality-vars.json
```

---

## Assertion Types Overview

| Type | Enum | Standalone Mutation | Monitor Mutation |
| --- | --- | --- | --- |
| Freshness | `FRESHNESS` | `createFreshnessAssertion` | `upsertDatasetFreshnessAssertionMonitor` |
| Volume | `VOLUME` | `createVolumeAssertion` | `upsertDatasetVolumeAssertionMonitor` |
| SQL | `SQL` | `createSqlAssertion` | `upsertDatasetSqlAssertionMonitor` |
| Field | `FIELD` | `createFieldAssertion` | `upsertDatasetFieldAssertionMonitor` |
| Schema | `DATA_SCHEMA` | — | `upsertDatasetSchemaAssertionMonitor` |
| Custom (external) | `CUSTOM` | `upsertCustomAssertion` | — |

**Standalone vs. Monitor:** Standalone creates the assertion definition only. Monitor creates the assertion AND attaches a cron schedule + executor so it runs automatically.

---

## Freshness Assertions

### Standalone

```graphql
mutation {
  createFreshnessAssertion(input: {
    entityUrn: "<DATASET_URN>"
    type: DATASET_CHANGE          # or DATA_JOB_RUN
    schedule: {
      type: FIXED_INTERVAL        # or CRON, SINCE_THE_LAST_CHECK
      fixedInterval: {
        unit: HOUR                # MINUTE, HOUR, DAY, WEEK, MONTH
        multiple: 6
      }
    }
    actions: {
      onFailure: [{ type: RAISE_INCIDENT }]
      onSuccess: [{ type: RESOLVE_INCIDENT }]
    }
  }) { urn }
}
```

### Monitor (with schedule)

```graphql
mutation {
  upsertDatasetFreshnessAssertionMonitor(input: {
    entityUrn: "<DATASET_URN>"
    schedule: {
      type: FIXED_INTERVAL
      fixedInterval: { unit: DAY, multiple: 1 }
    }
    evaluationSchedule: { cron: "0 9 * * *", timezone: "UTC" }
    evaluationParameters: { sourceType: INFORMATION_SCHEMA }
    mode: ACTIVE
    actions: {
      onFailure: [{ type: RAISE_INCIDENT }]
      onSuccess: [{ type: RESOLVE_INCIDENT }]
    }
  }) { urn }
}
```

### Smart (AI-inferred)

```graphql
mutation {
  upsertDatasetFreshnessAssertionMonitor(input: {
    entityUrn: "<DATASET_URN>"
    inferWithAI: true
    evaluationSchedule: { cron: "0 9 * * *", timezone: "UTC" }
    evaluationParameters: { sourceType: INFORMATION_SCHEMA }
    mode: ACTIVE
  }) { urn }
}
```

### Evaluation parameters (`DatasetFreshnessAssertionParametersInput`)

`evaluationParameters` is **required** on all freshness monitors. The `sourceType` tells DataHub how to detect changes:

| `DatasetFreshnessSourceType` | How it detects change | When to use |
| --- | --- | --- |
| `INFORMATION_SCHEMA` | Inspects system metadata tables | Snowflake, BigQuery, Redshift — fast, low overhead |
| `FIELD_VALUE` | Checks a timestamp column (requires `field` param) | When a reliable `updated_at` or `loaded_at` column exists |
| `AUDIT_LOG` | Inspects audit log API | When audit logging is available |
| `FILE_METADATA` | Inspects underlying file system | Data lakes, file-based sources |
| `DATAHUB_OPERATION` | Uses DataHub Operation aspect | When operations are reported to DataHub via ingestion |

**`FIELD_VALUE` example** — check freshness using a timestamp column:

```graphql
evaluationParameters: {
  sourceType: FIELD_VALUE
  field: { path: "updated_at", type: "TIMESTAMP", nativeType: "TIMESTAMP_NTZ" }
}
```

### Schedule types

| `FreshnessAssertionScheduleType` | Use case |
| --- | --- |
| `FIXED_INTERVAL` | "Should update every N hours/days" |
| `CRON` | "Should update by 9am every Monday" |
| `SINCE_THE_LAST_CHECK` | "Should have changed since the last assertion run" |

### Freshness types

| `FreshnessAssertionType` | Checks |
| --- | --- |
| `DATASET_CHANGE` | The dataset's audit stamp or operation log |
| `DATA_JOB_RUN` | A specific data job has run successfully |

---

## Volume Assertions

### Standalone

```graphql
mutation {
  createVolumeAssertion(input: {
    entityUrn: "<DATASET_URN>"
    type: ROW_COUNT_TOTAL
    rowCountTotal: {
      operator: GREATER_THAN
      parameters: { value: { value: "1000", type: NUMBER } }
    }
  }) { urn }
}
```

### Volume types

| `VolumeAssertionType` | Checks |
| --- | --- |
| `ROW_COUNT_TOTAL` | Absolute row count |
| `ROW_COUNT_CHANGE` | Row count change between evaluations |
| `INCREMENTING_SEGMENT_ROW_COUNT_TOTAL` | Rows in a time-partitioned segment |
| `INCREMENTING_SEGMENT_ROW_COUNT_CHANGE` | Row change in a time-partitioned segment |

### Volume monitor evaluation parameters

Volume monitors require `evaluationParameters` with `sourceType`:

| `DatasetVolumeSourceType` | How it counts rows | When to use |
| --- | --- | --- |
| `INFORMATION_SCHEMA` | Reads system metadata tables (fast, approximate) | Quick checks where exact count isn't critical |
| `QUERY` | Runs `COUNT(*)` query (exact, slower) | When exact row counts matter |
| `DATAHUB_DATASET_PROFILE` | Uses DataHub dataset profile aspect | When profiles are already collected |

```graphql
# Volume monitor example
mutation {
  upsertDatasetVolumeAssertionMonitor(input: {
    entityUrn: "<DATASET_URN>"
    type: ROW_COUNT_TOTAL
    rowCountTotal: { operator: GREATER_THAN, parameters: { value: { value: "1000", type: NUMBER } } }
    evaluationSchedule: { cron: "0 9 * * *", timezone: "UTC" }
    evaluationParameters: { sourceType: QUERY }
    mode: ACTIVE
  }) { urn }
}
```

### Operators (`AssertionStdOperator`)

`EQUAL_TO`, `NOT_EQUAL_TO`, `GREATER_THAN`, `GREATER_THAN_OR_EQUAL_TO`, `LESS_THAN`, `LESS_THAN_OR_EQUAL_TO`, `BETWEEN`, `NOT_NULL`, `NULL`, `IN`, `NOT_IN`, `CONTAIN`, `REGEX_MATCH`, `START_WITH`, `END_WITH`, `IS_TRUE`, `IS_FALSE`

---

## SQL Assertions

```graphql
mutation {
  createSqlAssertion(input: {
    entityUrn: "<DATASET_URN>"
    type: METRIC                  # or METRIC_CHANGE
    description: "No orphaned foreign keys"
    statement: "SELECT COUNT(*) FROM {dataset} d LEFT JOIN ref_table r ON d.ref_id = r.id WHERE r.id IS NULL"
    operator: EQUAL_TO
    parameters: {
      value: { value: "0", type: NUMBER }
    }
  }) { urn }
}
```

The `{dataset}` placeholder is replaced with the fully qualified table name at runtime.

### SQL Monitor (with schedule)

SQL monitors have **no `evaluationParameters`** — the SQL statement itself is the evaluation. DataHub runs it directly against the data warehouse.

```graphql
mutation {
  upsertDatasetSqlAssertionMonitor(input: {
    entityUrn: "<DATASET_URN>"
    type: METRIC
    description: "No orphaned foreign keys"
    statement: "SELECT COUNT(*) FROM {dataset} d LEFT JOIN ref_table r ON d.ref_id = r.id WHERE r.id IS NULL"
    operator: EQUAL_TO
    parameters: { value: { value: "0", type: NUMBER } }
    evaluationSchedule: { cron: "0 9 * * *", timezone: "UTC" }
    mode: ACTIVE
    actions: {
      onFailure: [{ type: RAISE_INCIDENT }]
      onSuccess: [{ type: RESOLVE_INCIDENT }]
    }
  }) { urn }
}
```

| `SqlAssertionType` | Checks |
| --- | --- |
| `METRIC` | The SQL returns a number; compare against threshold |
| `METRIC_CHANGE` | The SQL result change between evaluations |

---

## Field Assertions

### Field values (row-level checks)

```graphql
mutation {
  createFieldAssertion(input: {
    entityUrn: "<DATASET_URN>"
    type: FIELD_VALUES
    fieldValuesAssertion: {
      field: { path: "email", type: "STRING", nativeType: "VARCHAR" }
      operator: NOT_NULL
      excludeNulls: false
      failThreshold: { type: COUNT, value: 0 }
    }
  }) { urn }
}
```

`excludeNulls` is **required** on `FieldValuesAssertionInput`. Set to `true` to skip null rows before applying the operator, `false` to include them.

### Field metrics (aggregate checks)

```graphql
mutation {
  createFieldAssertion(input: {
    entityUrn: "<DATASET_URN>"
    type: FIELD_METRIC
    fieldMetricAssertion: {
      field: { path: "age", type: "NUMBER", nativeType: "INT" }
      metric: NULL_COUNT
      operator: LESS_THAN
      parameters: { value: { value: "10", type: NUMBER } }
    }
  }) { urn }
}
```

Note: `metric` is a flat `FieldMetricType!` enum, not an object. Use `metric: NULL_COUNT`, not `metric: { type: NULL_COUNT }`.

### Field monitor evaluation parameters

Field monitors require `evaluationParameters` with `sourceType`:

| `DatasetFieldAssertionSourceType` | How it evaluates | When to use |
| --- | --- | --- |
| `ALL_ROWS_QUERY` | Queries all rows in the table | Small-to-mid tables, or when full accuracy is needed |
| `CHANGED_ROWS_QUERY` | Only rows changed since last run (requires `changedRowsField`) | Large tables with a reliable `updated_at` column |
| `DATAHUB_DATASET_PROFILE` | Uses DataHub dataset profile | Field metrics only; when profiles are already collected |

**`CHANGED_ROWS_QUERY` example** — incremental field check using a timestamp column:

```graphql
evaluationParameters: {
  sourceType: CHANGED_ROWS_QUERY
  changedRowsField: { path: "updated_at", type: "TIMESTAMP", nativeType: "TIMESTAMP_NTZ" }
}
```

```graphql
# Field monitor example
mutation {
  upsertDatasetFieldAssertionMonitor(input: {
    entityUrn: "<DATASET_URN>"
    type: FIELD_METRIC
    fieldMetricAssertion: {
      field: { path: "email", type: "STRING", nativeType: "VARCHAR" }
      metric: NULL_PERCENTAGE
      operator: LESS_THAN
      parameters: { value: { value: "5", type: NUMBER } }
    }
    evaluationSchedule: { cron: "0 9 * * *", timezone: "UTC" }
    evaluationParameters: { sourceType: ALL_ROWS_QUERY }
    mode: ACTIVE
  }) { urn }
}
```

### Fail threshold types

| `FieldValuesFailThresholdType` | Meaning |
| --- | --- |
| `COUNT` | Absolute count of failing rows |
| `PERCENTAGE` | Percentage of failing rows (0-100) |

### Field metric types (`FieldMetricType`)

`NULL_COUNT`, `NULL_PERCENTAGE`, `UNIQUE_COUNT`, `UNIQUE_PERCENTAGE`, `MIN`, `MAX`, `MEAN`, `MEDIAN`, `STDDEV`, `NEGATIVE_COUNT`, `NEGATIVE_PERCENTAGE`, `ZERO_COUNT`, `ZERO_PERCENTAGE`, `MIN_LENGTH`, `MAX_LENGTH`, `EMPTY_COUNT`, `EMPTY_PERCENTAGE`

---

## Schema Assertions

Schema assertions are only available via monitor upsert (no standalone `createSchemaAssertion`). `evaluationParameters` is optional — the only source type is `DATAHUB_SCHEMA` (checks against DataHub's stored schema metadata), which is the default:

```graphql
mutation {
  upsertDatasetSchemaAssertionMonitor(input: {
    entityUrn: "<DATASET_URN>"
    assertion: {
      compatibility: SUPERSET
      fields: [
        { path: "id", type: NUMBER },
        { path: "email", type: STRING },
        { path: "created_at", type: DATE }
      ]
    }
    evaluationSchedule: { cron: "0 9 * * *", timezone: "UTC" }
    mode: ACTIVE
  }) { urn }
}
```

| `SchemaAssertionCompatibility` | Meaning |
| --- | --- |
| `EXACT_MATCH` | Schema must match exactly |
| `SUPERSET` | Actual schema must contain all expected fields (may have extras) |
| `SUBSET` | Expected fields must be a subset of actual schema |

---

## Custom / External Assertions

Register assertions from external tools (Great Expectations, dbt tests, Soda, Monte Carlo):

```graphql
mutation {
  upsertCustomAssertion(input: {
    entityUrn: "<DATASET_URN>"
    type: "Row Count Check"
    description: "Checks row count is above threshold"
    platform: { urn: "urn:li:dataPlatform:greatExpectations" }
    fieldPath: "order_id"
    externalUrl: "https://ge.company.com/validations/123"
    logic: "expect_table_row_count_to_be_between(min=1000)"
  }) { urn }
}
```

Note: `platform` is `PlatformInput!` (an object with `urn` and/or `name`), not a bare string.

Then push results with `reportAssertionResult`:

```graphql
mutation {
  reportAssertionResult(
    urn: "<ASSERTION_URN>"
    result: {
      timestampMillis: 1700000000000
      type: SUCCESS
      properties: [
        { key: "observed_value", value: "52340" }
        { key: "expectation", value: "expect_table_row_count_to_be_between" }
      ]
    }
  )
}
```

### Result types (`AssertionResultType`)

| Value | Meaning |
| --- | --- |
| `SUCCESS` | Assertion passed |
| `FAILURE` | Assertion failed |
| `ERROR` | Assertion could not be evaluated |
| `INIT` | Initial state, no result yet |

---

## Running Assertions

```graphql
# Single assertion
mutation {
  runAssertion(urn: "<ASSERTION_URN>", saveResult: true) {
    type
    nativeResults { key value }
  }
}

# Multiple assertions
mutation {
  runAssertions(urns: ["<URN1>", "<URN2>"], saveResults: true) {
    passingCount
    failingCount
    errorCount
    results {
      assertion { urn info { type } }
      result { type }
    }
  }
}

# All assertions for an asset
mutation {
  runAssertionsForAsset(urn: "<DATASET_URN>") {
    passingCount failingCount errorCount
    results {
      assertion { urn info { type description } }
      result { type }
    }
  }
}
```

`saveResult: true` persists the result (default).

**Native assertions only.** The run mutations only work on native assertions (created via `create*Assertion` or `upsertDataset*AssertionMonitor`). External assertions from dbt, Great Expectations, Soda, Monte Carlo, etc. (registered via `upsertCustomAssertion`) **cannot be run on demand** — they are evaluated by their external tool, and results are pushed to DataHub via `reportAssertionResult`.

**Async mode:** All run mutations have a **30-second timeout**. Field/column validation checks on large tables can easily exceed this. Pass `async: true` to return immediately, then poll `assertion.runEvents` for results — this is how the UI runs assertions. Use async for field checks, SQL checks on large tables, or when running many assertions at once. Max 20 assertions per call.

---

## Deleting Assertions

```graphql
mutation {
  deleteAssertion(urn: "<ASSERTION_URN>")
}
```

---

## Assertion Actions

Attach automated responses to assertion outcomes:

```graphql
actions: {
  onFailure: [{ type: RAISE_INCIDENT }]
  onSuccess: [{ type: RESOLVE_INCIDENT }]
}
```

| `AssertionActionType` | Effect |
| --- | --- |
| `RAISE_INCIDENT` | Automatically creates an incident on the asset |
| `RESOLVE_INCIDENT` | Automatically resolves related incidents when the assertion passes |

Include `actions` in any `create*Assertion` or `upsertDataset*AssertionMonitor` input.
