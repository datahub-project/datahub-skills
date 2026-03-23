# Planning Document Sections Guide

## Contents

- [Load Standards First](#load-standards-first)
- [Load Reference Documents](#load-reference-documents)
- [Section 1: Source System Overview](#section-1-source-system-overview)
- [Section 2: Entity Mapping Table](#section-2-entity-mapping-table)
- [Section 3: Architecture Decisions](#section-3-architecture-decisions)
- [Section 4: Capabilities to Implement](#section-4-capabilities-to-implement)
- [Section 5: Configuration Design](#section-5-configuration-design)
- [Section 6: Testing Strategy](#section-6-testing-strategy)
- [Section 7: Known Limitations](#section-7-known-limitations)
- [Section 8: Implementation Order](#section-8-implementation-order)

## Load Standards First

Before creating the planning document, read the relevant golden standards:

**Core standards (always load):**

```
Read standards/main.md
Read standards/containers.md
Read standards/patterns.md
Read standards/testing.md
```

**Source-type specific standards:**

- For SQL sources: `standards/sql.md`
- For API sources: `standards/api.md`
- If lineage needed: `standards/lineage.md`

**Source-category standards:**

- `standards/[standards_file from classification]` (e.g., `standards/source_types/sql_databases.md`)

## Load Reference Documents

Read the relevant reference docs from this skill:

- `references/two-tier-vs-three-tier.md` (for SQL sources — base class selection)
- `references/capability-mapping.md` (for mapping features to @capability decorators)
- `references/testing-patterns.md` (for test strategy)
- `references/mce-vs-mcp-formats.md` (for understanding output format expectations)

## Section 1: Source System Overview

- Type classification (from Step 1)
- Authentication method
- API/SDK documentation links
- Docker image for testing (if available)

## Section 2: Entity Mapping Table

Map source concepts to DataHub entities. Consult `standards/containers.md` for container hierarchy patterns. Select the mapping table from the template that matches the source category. The template (`templates/planning-doc.template.md`) provides entity mapping tables for each category:

- **SQL sources** (sql_databases, data_warehouses, query_engines, data_lakes): Database/Schema/Table/View/Column
- **BI tools** (bi_tools, product_analytics): Workspace/Folder/Dashboard/Chart/Data Source
- **Orchestration tools**: DAG/Pipeline/Task/Input-Output Datasets
- **Streaming platforms**: Cluster/Topic/Schema/Consumer Group
- **ML platforms**: Project/Model Group/Model Version/Training Dataset
- **Identity platforms**: User/Group/Group Membership
- **NoSQL databases**: Database/Collection/Fields (via schema inference)

For each entity, fill in the actual source concept name (e.g., for Tableau: "Workbook" maps to Dashboard, "Sheet" maps to Chart). Look up `references/source-type-mapping.yml` for the expected entities and aspects per category.

## Section 3: Architecture Decisions

**Base class selection** — Reference `standards/main.md` and the template's Architecture Decisions section:

For SQL sources — Reference [two-tier-vs-three-tier.md](references/two-tier-vs-three-tier.md):

- `TwoTierSQLAlchemySource` -- schema.table hierarchy (DuckDB, ClickHouse, MySQL)
- `SQLAlchemySource` -- database.schema.table hierarchy (PostgreSQL, Snowflake)
- `StatefulIngestionSourceBase` -- custom implementation when no SQLAlchemy dialect exists

For API sources (BI, orchestration, streaming, ML, identity, analytics) — Reference `standards/api.md`:

- `StatefulIngestionSourceBase` -- standard for all API connectors
- **Client class design** (`client.py`): Separate API client class that encapsulates all HTTP communication
  - Use **Pydantic models** for API response parsing and validation
  - Implement **pagination** (determine cursor-based, offset-based, or page-based from API docs)
  - Implement **rate limiting** (token bucket or retry-with-exponential-backoff)
  - Handle **authentication** per source API (OAuth2 flow, API key header, bearer token)
  - Design **error handling** with retries for transient failures (429, 5xx)

For NoSQL sources — Reference `standards/source_types/nosql_databases.md`:

- `StatefulIngestionSourceBase` -- standard for NoSQL connectors
- Use the **native driver** (e.g., `pymongo` for MongoDB, `cassandra-driver` for Cassandra, `boto3` for DynamoDB)
- **Schema inference**: Sample N documents/rows to infer schema fields and types
  - Configurable sample size (default: 1000)
  - Handle schema evolution (merge fields across samples)
  - Map native types to DataHub SchemaFieldDataType

**Config design** — Reference `standards/patterns.md`:

- What config class to inherit from (per source type, see template)
- Custom fields needed
- Validation rules

## Section 4: Capabilities to Implement

Reference `references/capability-mapping.md` for mapping features to `@capability` decorators. Select the capability table from the template that matches the source category:

- **SQL sources**: SCHEMA_METADATA, CONTAINERS, LINEAGE_COARSE, LINEAGE_FINE, DATA_PROFILING, USAGE_STATS
- **BI tools**: DASHBOARDS, CHARTS, LINEAGE_COARSE (dashboard-to-dataset), CONTAINERS, OWNERSHIP, TAGS
- **Orchestration**: DATA_FLOW, DATA_JOB, LINEAGE_COARSE (job I/O), OWNERSHIP, TAGS
- **Streaming**: SCHEMA_METADATA (from schema registry), CONTAINERS, LINEAGE_COARSE
- **ML platforms**: ML_MODELS, ML_MODEL_GROUPS, CONTAINERS, LINEAGE_COARSE (model-to-dataset)
- **Identity**: CORP_USERS, CORP_GROUPS, GROUP_MEMBERSHIP
- **NoSQL**: SCHEMA_METADATA (via inference), CONTAINERS

Mark each capability as Required / Per user scope / Optional based on the user's chosen feature scope from Step 2. Look up the full per-category capability tables in the template.

## Section 5: Configuration Design

Use the config example from the template matching the source type. The three patterns are:

**SQL sources** -- connection string + schema/table filtering:

```yaml
source:
  type: SOURCE_NAME
  config:
    host_port: "localhost:5432"
    database: my_database
    username: datahub
    password: ${DATAHUB_PASSWORD}
    schema_pattern:
      allow: ["public"]
    table_pattern:
      deny: ["_tmp_.*"]
```

**API sources** -- base_url + auth + entity filtering:

```yaml
source:
  type: SOURCE_NAME
  config:
    base_url: "https://api.example.com"
    api_key: ${SOURCE_API_KEY} # or token, or OAuth client_id/secret
    project_pattern:
      allow: ["prod-*"]
```

**NoSQL sources** -- connect_uri + schema inference settings:

```yaml
source:
  type: SOURCE_NAME
  config:
    connect_uri: "mongodb://localhost:27017"
    database_pattern:
      allow: ["prod_*"]
    collection_pattern:
      deny: ["system\\..*"]
    schema_inference:
      enabled: true
      sample_size: 1000
```

Customize the config fields based on the specific source system's connection requirements.

## Section 6: Testing Strategy

Reference `standards/testing.md` and [testing-patterns.md](references/testing-patterns.md):

| Test Type              | Requirements                                         | Location                           |
| ---------------------- | ---------------------------------------------------- | ---------------------------------- |
| Unit tests             | >=80% coverage, config validation, entity extraction | `tests/unit/test_SOURCE_source.py` |
| Integration tests      | Golden file with real data, >5KB, >20 events         | `tests/integration/SOURCE/`        |
| Golden file validation | schemaMetadata for datasets, container hierarchy     | Via `extract_aspects.py`           |

## Section 7: Known Limitations

| Limitation                   | Impact | Workaround |
| ---------------------------- | ------ | ---------- |
| (list any known constraints) |        |            |

## Section 8: Implementation Order

Select the implementation order from the template matching the source type:

**For SQL sources:**

1. Config classes (`config.py`)
2. Source class with table/view extraction (`source.py`)
3. Register in setup entry points
4. View extraction + container hierarchy
5. Unit tests
6. Lineage from view definitions (if in scope)
7. Usage statistics (data warehouses only, if in scope)
8. Integration tests with golden files
9. Documentation

**For API sources:**

1. API client class with auth, pagination, rate limiting (`client.py`)
2. Pydantic response models
3. Config classes (`config.py`)
4. Source class with primary entity extraction (`source.py`)
5. Register in setup entry points
6. Container hierarchy (workspaces/projects/folders)
7. Unit tests (with mocked API responses)
8. Lineage (if in scope)
9. Ownership and tags (if in scope)
10. Integration tests with golden files
11. Documentation

**For NoSQL sources:**

1. Config classes with schema inference settings (`config.py`)
2. Schema inference implementation
3. Source class with collection/table extraction (`source.py`)
4. Register in setup entry points
5. Container hierarchy (databases/keyspaces)
6. Unit tests
7. Integration tests with golden files
8. Documentation
