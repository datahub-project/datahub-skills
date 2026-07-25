# Data Contract YAML Reference

The declarative format parsed by `datahub.api.entities.datacontract.DataContract` (`from_yaml`). This is the native, supported path for authoring a DataHub `dataContract`. The deprecated `datahub datacontract` CLI is **not** used.

## Top-level keys

| Key            | Required | Description                                                                  |
| -------------- | -------- | ---------------------------------------------------------------------------- |
| `version`      | yes      | Must be `1`.                                                                 |
| `entity`       | yes      | The dataset URN the contract is bound to.                                    |
| `id` / `urn`   | no       | The contract URN. If omitted, a stable GUID is generated from the entity.    |
| `schema`       | no       | A single schema assertion.                                                   |
| `freshness`    | no       | A single freshness assertion.                                                |
| `data_quality` | no       | A list of data-quality assertions (volume, uniqueness, null, custom metric). |
| `properties`   | no       | Structured properties to attach to the contract (`{key: value}`).            |

At least one of `schema`, `freshness`, or `data_quality` should be present.

## `schema`

Two forms:

**`json-schema`** — clean to author; converted to DataHub schema metadata internally:

```yaml
schema:
  type: json-schema
  json-schema:
    type: object
    properties:
      id:
        type: integer
        native_type: NUMBER
      email:
        type: string
        native_type: VARCHAR
    required: [id, email]
```

**`field-list`** — mirrors DataHub's native `SchemaField` shape:

```yaml
schema:
  type: field-list
  fields:
    - fieldPath: id
      type:
        type:
          com.linkedin.schema.NumberType: {}
      nativeDataType: NUMBER
    - fieldPath: email
      type:
        type:
          com.linkedin.schema.StringType: {}
      nativeDataType: VARCHAR
```

Prefer `json-schema` for authored contracts; use `field-list` when copying the dataset's exact native schema.

## `freshness`

**`cron`** — the table should update on a schedule:

```yaml
freshness:
  type: cron
  cron: "0 8 * * *" # see https://crontab.guru/
  timezone: UTC # optional, defaults to UTC
```

**`interval`** — the table should update at least this often (ISO-8601 duration):

```yaml
freshness:
  type: interval
  interval: 86400 # seconds, or an ISO-8601 duration like PT24H
```

## `data_quality`

A list. Each entry is one of:

**`custom_sql`** — a SQL metric compared to a threshold. This is how **volume**, **not-null**, and any custom metric are expressed:

```yaml
data_quality:
  # Volume: row count within a band
  - type: custom_sql
    description: row count stays within the expected band
    sql: "SELECT COUNT(*) FROM analytics.purchases"
    operator:
      type: between
      min: 120000
      max: 180000
  # Not-null: zero null ids
  - type: custom_sql
    description: id is never null
    sql: "SELECT COUNT(*) FROM analytics.purchases WHERE id IS NULL"
    operator:
      type: equal_to
      value: 0
```

**`unique`** — a column's values are unique:

```yaml
data_quality:
  - type: unique
    column: id
```

### Operators (for `custom_sql`)

| Operator                   | Fields       |
| -------------------------- | ------------ |
| `equal_to`                 | `value`      |
| `between`                  | `min`, `max` |
| `less_than`                | `value`      |
| `greater_than`             | `value`      |
| `less_than_or_equal_to`    | `value`      |
| `greater_than_or_equal_to` | `value`      |
| `not_null`                 | (none)       |

### Ids

Each `data_quality` entry gets an id from its explicit `id`, or a generated one from its type/column/sql. **Two entries that generate the same id are rejected at parse time** — give near-identical checks a distinct `id` or `description`.

## What `generate_mcp()` produces

For a parsed contract, `contract.generate_mcp()` yields, with stable URNs:

- one `AssertionInfo` MCP per `schema` / `freshness` / `data_quality` entry,
- a `DataContractProperties` aspect binding those assertion URNs under `schema` / `freshness` / `dataQuality`,
- a `Status(removed=False)` aspect,
- a `DataContractStatus(state=PENDING)` aspect,
- a `StructuredProperties` aspect if `properties` were set.

Emit each MCP with `graph.emit_mcp(mcp)`. Activate the contract afterward by emitting `DataContractStatus(state=ACTIVE)`.
