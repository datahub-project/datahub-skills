# Configuration Schema

Full schema for DataHub agent configuration profiles.

## File Format

Profiles are YAML files: `.datahub-agent-config.yml` (default) or `.datahub-agent-config.<name>.yml` (named).

## Schema

```yaml
# Required
name: string              # Profile name (alphanumeric, hyphens, underscores)
description: string       # Human-readable purpose

# Scope filters — applied as defaults to search, audit, and other skills
scope:
  platforms: string[]     # e.g., ["snowflake", "bigquery"]. Empty = all.
  domains: string[]       # e.g., ["Finance"]. Empty = all.
  entity_types: string[]  # e.g., ["dataset", "dashboard"]. Empty = all.
  environment: string     # e.g., "PROD". Empty = all.

# Search behavior
search:
  default_count: integer  # Results per query (1-100, default: 10)
  exclude_deprecated: boolean  # Hide deprecated entities (default: false)
  exclude_soft_deleted: boolean  # Hide soft-deleted entities (default: true)

# Access scope
owner_filter: string      # Filter by owner URN. Empty = no filter.
```

## Example Profiles

### Data engineering team

```yaml
name: data-eng
description: "Data engineering — all platforms, datasets and pipelines"
scope:
  platforms: []
  domains: []
  entity_types: [dataset, dataFlow, dataJob]
  environment: "PROD"
search:
  default_count: 20
  exclude_deprecated: true
  exclude_soft_deleted: true
owner_filter: "urn:li:corpGroup:data-eng"
```

### Finance analyst

```yaml
name: finance-analyst
description: "Finance domain — Snowflake datasets and Looker dashboards"
scope:
  platforms: [snowflake, looker]
  domains: [Finance]
  entity_types: [dataset, dashboard, chart]
  environment: "PROD"
search:
  default_count: 10
  exclude_deprecated: false
  exclude_soft_deleted: true
owner_filter: ""
```
