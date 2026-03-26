# Search Filter Reference

## Available Filters

| Filter | Description | Example Values |
| --- | --- | --- |
| `platform` | Data platform | `snowflake`, `bigquery`, `redshift`, `postgres`, `looker`, `tableau`, `airflow` |
| `env` | Environment | `PROD`, `DEV`, `STAGING`, `TEST` |
| `entity_type` | Entity type | `dataset`, `dashboard`, `chart`, `dataFlow`, `dataJob`, `container` |
| `domain` | Business domain | Domain URN |
| `tag` | Tags applied | Tag URN (e.g., `urn:li:tag:pii`) |
| `glossary_term` | Glossary terms | Term URN |
| `owners` | Entity owners | User/group URN |
| `container` | Parent container | Container URN |
| `fieldPaths` | Column/field names (datasets) | Field name (e.g., `customer_id`, `email`) |

Use `datahub search list-filters` to discover all available filters.
Use `datahub search describe-filter <name>` for details on a specific filter.

## Simple Filter Syntax (`--filter`)

```bash
# Single filter
datahub search "revenue" --filter platform=snowflake

# Multiple values on same field (OR)
datahub search "*" --filter platform=snowflake,bigquery

# Multiple filter fields (AND)
datahub search "*" --filter platform=snowflake --filter env=PROD
```

## SQL-Like WHERE Syntax (`--where`) — Recommended for Agents

```bash
# AND
datahub search "*" --where "platform = snowflake AND env = PROD"

# OR
datahub search "*" --where "platform = snowflake OR platform = bigquery"

# IN
datahub search "*" --where "platform IN (snowflake, bigquery)"

# NOT
datahub search "*" --where "NOT env = DEV"

# IS NULL / IS NOT NULL
datahub search "*" --where "glossary_term IS NOT NULL"

# Combined
datahub search "*" --where "entity_type = dataset AND platform = snowflake AND env = PROD"
```

## Complex JSON Filters (`--filters`)

For AND/OR/NOT logic that's hard to express in `--where`:

```json
{"and": [{"platform": ["snowflake"]}, {"env": ["PROD"]}]}
```

## Field-Level Search (`fieldPaths`)

To find datasets that contain a column matching a given name, use `fieldPaths`. This searches against the indexed column names in `schemaMetadata`. You can use it either as a query prefix or as a `--where` filter field.

```bash
# As a WHERE filter (recommended — combines cleanly with other filters)
datahub search "*" --where "entity_type = dataset AND fieldPaths = customer_id"

# With platform filter
datahub search "*" --where "entity_type = dataset AND platform = snowflake AND fieldPaths = email"

# With environment
datahub search "*" --where "entity_type = dataset AND env = PROD AND fieldPaths = revenue"

# As a query prefix (also works)
datahub search "fieldPaths:customer_id" --where "entity_type = dataset"
```

The match is token-based — `fieldPaths = customer_id` matches columns named `customer_id`, `root.customer_id`, etc. It does not do substring matching within a single token, so `fieldPaths = cust` will not match `customer_id`.

## Structured Property Filters

Structured properties are custom metadata fields defined by admins. They can be attached to datasets, containers, and other entity types. Filtering by structured property values requires a two-step process.

### Step 1: Find the structured property ID

Search for the structured property definition by entity type:

```bash
# Find a structured property by name
datahub search "data tier" --where "entity_type = structuredProperty" --format json --limit 5

# Get all structured properties
datahub search "*" --where "entity_type = structuredProperty" --format json --limit 50
```

The result gives you the property's qualified name (the field ID), e.g., `io.acryl.dataTier`.

If the property has **allowed values** (an enumeration), fetch the full property definition to see them:

```bash
datahub get --urn "urn:li:structuredProperty:io.acryl.dataTier"
```

Look for `allowedValues` in the response — these are the only valid filter values for that property.

### Step 2: Filter by structured property value

Use the filter field `structuredProperties.<fieldId>` with an exact-match value:

```bash
# Simple filter
datahub search "*" --filter "structuredProperties.io.acryl.dataTier=Tier 1"

# WHERE syntax
datahub search "*" --where "entity_type = dataset AND structuredProperties.io.acryl.dataTier = 'Tier 1'"

# Combine with other filters
datahub search "*" --where "entity_type = dataset AND platform = snowflake AND structuredProperties.io.acryl.dataTier = 'Tier 1'"
```

**Important:** Structured property filter values must be exact matches — partial or fuzzy matching is not supported. If the property uses allowed values, the filter value must exactly match one of them.

## Tips

- **Wildcard search:** `*` matches all entities (useful when filtering by metadata)
- **Max 50 results per page.** Use `--limit` and `--offset` for pagination.
- **Dry run:** `--dry-run` previews the compiled query without executing.
- **Facets:** `--facets-only` returns counts by type/platform/etc. without results.
- **`--filter`, `--where`, and `--filters` are mutually exclusive** — use one at a time.
