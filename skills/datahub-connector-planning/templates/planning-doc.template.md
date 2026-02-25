# {{ source_name }} Connector - Planning Document

**Created**: {{ date }}
**Status**: IN_PROGRESS | APPROVED | COMPLETE

## Overview

Brief description of the source system and connector goals.

## Research Summary

### Source Classification

- **Type**: SQL Database / API / NoSQL / Other
- **Source Category**: {{ source_category }} (e.g., sql_databases, bi_tools, streaming_platforms)
- **Interface**: SQLAlchemy dialect / REST API / GraphQL / Native SDK / etc.
- **Standards File**: `standards/{{ standards_file }}` (e.g., `standards/source_types/sql_databases.md`)
- **Documentation**: [Link to official docs]

### Similar DataHub Connectors

| Connector  | Relevance | Key Patterns        |
| ---------- | --------- | ------------------- |
| connector1 | High      | Pattern description |
| connector2 | Medium    | Pattern description |

## Entity Mapping

<!-- Select the entity mapping table that matches the source category from Step 1. -->

### For SQL sources (sql_databases, data_warehouses, query_engines, data_lakes)

| Source Concept   | DataHub Entity | Entity Subtype | URN Format                                                   | Notes                 |
| ---------------- | -------------- | -------------- | ------------------------------------------------------------ | --------------------- |
| Database/Catalog | Container      | Database       | `urn:li:container:...`                                       | Top-level container   |
| Schema/Namespace | Container      | Schema         | `urn:li:container:...`                                       | Nested under database |
| Table            | Dataset        | Table          | `urn:li:dataset:(urn:li:dataPlatform:{{ source_name }},...)` |                       |
| View             | Dataset        | View           | `urn:li:dataset:(urn:li:dataPlatform:{{ source_name }},...)` | subTypes=["View"]     |
| Column           | SchemaField    | --             | Embedded in Dataset                                          |                       |

### For BI tools (bi_tools, product_analytics)

| Source Concept    | DataHub Entity | Entity Subtype | URN Format                                                     | Notes                            |
| ----------------- | -------------- | -------------- | -------------------------------------------------------------- | -------------------------------- |
| Workspace/Project | Container      | --             | `urn:li:container:...`                                         | Top-level container              |
| Folder/Collection | Container      | --             | `urn:li:container:...`                                         | Nested container (optional)      |
| Dashboard         | Dashboard      | --             | `urn:li:dashboard:(urn:li:dataPlatform:{{ source_name }},...)` |                                  |
| Chart/Widget      | Chart          | --             | `urn:li:chart:(urn:li:dataPlatform:{{ source_name }},...)`     | Linked to dashboard              |
| Data Source       | Dataset        | --             | `urn:li:dataset:(urn:li:dataPlatform:{{ source_name }},...)`   | For lineage to upstream datasets |

### For orchestration tools (orchestration_tools)

| Source Concept       | DataHub Entity | Entity Subtype | URN Format                                     | Notes                                              |
| -------------------- | -------------- | -------------- | ---------------------------------------------- | -------------------------------------------------- |
| DAG/Pipeline         | DataFlow       | --             | `urn:li:dataFlow:({{ source_name }},...)`      |                                                    |
| Task/Operator        | DataJob        | --             | `urn:li:dataJob:(urn:li:dataFlow:...,...)`     | Nested under DataFlow                              |
| Input/Output Dataset | Dataset        | --             | `urn:li:dataset:(urn:li:dataPlatform:...,...)` | For job lineage (may reference external platforms) |

### For streaming platforms (streaming_platforms)

| Source Concept | DataHub Entity | Entity Subtype | URN Format                                                   | Notes                             |
| -------------- | -------------- | -------------- | ------------------------------------------------------------ | --------------------------------- |
| Cluster        | Container      | --             | `urn:li:container:...`                                       | Top-level container               |
| Topic          | Dataset        | Topic          | `urn:li:dataset:(urn:li:dataPlatform:{{ source_name }},...)` | subTypes=["Topic"]                |
| Schema         | SchemaField    | --             | Embedded in Dataset                                          | From schema registry if available |
| Consumer Group | --             | --             | --                                                           | Metadata on dataset (optional)    |

### For ML platforms (ml_platforms)

| Source Concept     | DataHub Entity | Entity Subtype | URN Format                                                        | Notes                                          |
| ------------------ | -------------- | -------------- | ----------------------------------------------------------------- | ---------------------------------------------- |
| Project/Experiment | Container      | --             | `urn:li:container:...`                                            | Top-level container                            |
| Model Group        | MLModelGroup   | --             | `urn:li:mlModelGroup:(urn:li:dataPlatform:{{ source_name }},...)` |                                                |
| Model Version      | MLModel        | --             | `urn:li:mlModel:(urn:li:dataPlatform:{{ source_name }},...)`      | Linked to group                                |
| Training Dataset   | Dataset        | --             | `urn:li:dataset:(urn:li:dataPlatform:...,...)`                    | For lineage (may reference external platforms) |

### For identity platforms (identity_platforms)

| Source Concept   | DataHub Entity | Entity Subtype | URN Format             | Notes                              |
| ---------------- | -------------- | -------------- | ---------------------- | ---------------------------------- |
| User             | CorpUser       | --             | `urn:li:corpuser:...`  |                                    |
| Group/Role       | CorpGroup      | --             | `urn:li:corpGroup:...` |                                    |
| Group Membership | --             | --             | --                     | groupMembership aspect on CorpUser |

### For NoSQL databases (nosql_databases)

| Source Concept    | DataHub Entity | Entity Subtype | URN Format                                                   | Notes                                   |
| ----------------- | -------------- | -------------- | ------------------------------------------------------------ | --------------------------------------- |
| Database/Keyspace | Container      | Database       | `urn:li:container:...`                                       | Top-level container                     |
| Collection/Table  | Dataset        | --             | `urn:li:dataset:(urn:li:dataPlatform:{{ source_name }},...)` |                                         |
| Fields            | SchemaField    | --             | Embedded in Dataset                                          | Via schema inference (sample documents) |

## Architecture Decisions

### Base Class Selection

<!-- Select the section matching your source type. -->

#### For SQL sources

- `TwoTierSQLAlchemySource` -- schema.table hierarchy (DuckDB, ClickHouse, MySQL)
- `SQLAlchemySource` -- database.schema.table hierarchy (PostgreSQL, Snowflake)
- `StatefulIngestionSourceBase` -- custom implementation when no SQLAlchemy dialect exists

**Chosen**: {{ chosen_base_class }}
**Rationale**: {{ rationale }}

Reference: `references/two-tier-vs-three-tier.md`, `standards/sql.md`

#### For API sources (bi_tools, orchestration, streaming, ML, identity, analytics)

- `StatefulIngestionSourceBase` -- standard for all API connectors
- Requires a separate **client class** (`client.py`) for API communication
- Use **Pydantic models** for API response parsing
- Implement **pagination** (cursor-based, offset-based, or page-based as per API)
- Implement **rate limiting** (token bucket or retry-with-backoff)
- Handle **authentication** (OAuth2, API key, token — as per source API)

**Chosen**: `StatefulIngestionSourceBase`
**Client class**: `{{ source_name }}_client.py` or `client.py`
**Auth method**: {{ auth_method }}

Reference: `standards/api.md`

#### For NoSQL sources

- `StatefulIngestionSourceBase` -- standard for NoSQL connectors
- Use the **native driver** (e.g., `pymongo`, `cassandra-driver`, `boto3`)
- Implement **schema inference** by sampling documents/rows
- Configure **sample size** (default: 1000 documents) for schema inference

**Chosen**: `StatefulIngestionSourceBase`
**Driver**: {{ native_driver }}
**Schema inference**: Yes / No (has schema registry)

Reference: `standards/api.md`, `standards/source_types/nosql_databases.md`

### Config Structure

<!-- Select the config example matching your source type. -->

#### For SQL sources

- Inherits from: `TwoTierSQLAlchemyConfig` / `BasicSQLAlchemyConfig` / `StatefulIngestionConfigBase`
- Custom fields: List any source-specific config fields

```yaml
source:
  type: { { source_name } }
  config:
    host_port: "localhost:5432"
    database: my_database
    username: datahub
    password: ${DATAHUB_PASSWORD}
    # Schema/table filtering
    schema_pattern:
      allow: ["public"]
    table_pattern:
      deny: ["_tmp_.*"]
```

#### For API sources

- Inherits from: `StatefulIngestionConfigBase`
- Custom fields: base_url, authentication, pagination, filters

```yaml
source:
  type: { { source_name } }
  config:
    base_url: "https://api.example.com"
    # Authentication (pick one pattern)
    api_key: ${SOURCE_API_KEY}
    # -- or --
    token: ${SOURCE_TOKEN}
    # -- or --
    client_id: ${SOURCE_CLIENT_ID}
    client_secret: ${SOURCE_CLIENT_SECRET}
    # Filtering
    project_pattern:
      allow: ["prod-*"]
```

#### For NoSQL sources

- Inherits from: `StatefulIngestionConfigBase`
- Custom fields: connect_uri, schema inference settings

```yaml
source:
  type: { { source_name } }
  config:
    connect_uri: "mongodb://localhost:27017"
    database_pattern:
      allow: ["prod_*"]
    collection_pattern:
      deny: ["system\\..*"]
    # Schema inference
    schema_inference:
      enabled: true
      sample_size: 1000
      max_schema_size: 300 # max fields
```

### Capabilities to Implement

<!-- Select the capability table matching your source category. -->

#### For SQL sources (sql_databases, data_warehouses, query_engines, data_lakes)

| Capability        | Priority       | Implementation Notes                    |
| ----------------- | -------------- | --------------------------------------- |
| SCHEMA_METADATA   | Required       | Via SQLAlchemy base class               |
| CONTAINERS        | Required       | Database + Schema containers            |
| LINEAGE_COARSE    | Per user scope | From view definitions                   |
| LINEAGE_FINE      | Optional       | Column-level if feasible                |
| DATA_PROFILING    | Optional       | Via Great Expectations                  |
| USAGE_STATS       | Optional       | Data warehouses only -- from query logs |
| PLATFORM_INSTANCE | Optional       | Multi-instance support                  |

#### For BI tools (bi_tools, product_analytics)

| Capability        | Priority | Implementation Notes                        |
| ----------------- | -------- | ------------------------------------------- |
| DASHBOARDS        | Required | Dashboard metadata extraction               |
| CHARTS            | Required | Chart/widget extraction                     |
| LINEAGE_COARSE    | Required | Dashboard/chart to upstream dataset lineage |
| CONTAINERS        | Required | Workspace/folder hierarchy                  |
| OWNERSHIP         | Optional | Dashboard/chart owners                      |
| TAGS              | Optional | Native labels/categories                    |
| PLATFORM_INSTANCE | Optional | Multi-instance support                      |

#### For orchestration tools (orchestration_tools)

| Capability        | Priority | Implementation Notes     |
| ----------------- | -------- | ------------------------ |
| DATA_FLOW         | Required | DAG/pipeline extraction  |
| DATA_JOB          | Required | Task/operator extraction |
| LINEAGE_COARSE    | Required | Job input/output lineage |
| OWNERSHIP         | Optional | Pipeline/task owners     |
| TAGS              | Optional | Native labels            |
| PLATFORM_INSTANCE | Optional | Multi-instance support   |

#### For streaming platforms (streaming_platforms)

| Capability        | Priority | Implementation Notes                              |
| ----------------- | -------- | ------------------------------------------------- |
| SCHEMA_METADATA   | Required | Topic schemas (from schema registry if available) |
| CONTAINERS        | Required | Cluster/namespace hierarchy                       |
| LINEAGE_COARSE    | Optional | Producer/consumer lineage                         |
| PLATFORM_INSTANCE | Optional | Multi-cluster support                             |

#### For ML platforms (ml_platforms)

| Capability        | Priority | Implementation Notes              |
| ----------------- | -------- | --------------------------------- |
| ML_MODELS         | Required | Model + version extraction        |
| ML_MODEL_GROUPS   | Required | Model group/project extraction    |
| CONTAINERS        | Required | Project/experiment hierarchy      |
| LINEAGE_COARSE    | Optional | Model to training dataset lineage |
| OWNERSHIP         | Optional | Model owners                      |
| PLATFORM_INSTANCE | Optional | Multi-instance support            |

#### For identity platforms (identity_platforms)

| Capability        | Priority | Implementation Notes   |
| ----------------- | -------- | ---------------------- |
| CORP_USERS        | Required | User extraction        |
| CORP_GROUPS       | Required | Group/role extraction  |
| GROUP_MEMBERSHIP  | Required | User-to-group mapping  |
| PLATFORM_INSTANCE | Optional | Multi-instance support |

#### For NoSQL databases (nosql_databases)

| Capability        | Priority | Implementation Notes                      |
| ----------------- | -------- | ----------------------------------------- |
| SCHEMA_METADATA   | Required | Via schema inference (sampling documents) |
| CONTAINERS        | Required | Database/keyspace containers              |
| PLATFORM_INSTANCE | Optional | Multi-instance support                    |

## Known Limitations

| Limitation          | Impact      | Workaround    |
| ------------------- | ----------- | ------------- |
| Describe limitation | User impact | How to handle |

## Implementation Plan

<!-- Select the implementation order matching your source type. -->

### For SQL sources

#### Phase 1: Basic Extraction

- [ ] Create `config.py` with connection config
- [ ] Create `source.py` with table/view extraction
- [ ] Register in setup.py entry points
- [ ] Verify basic extraction works

#### Phase 2: Additional Features

- [ ] View extraction + container hierarchy
- [ ] Lineage from view definitions (if applicable)
- [ ] Usage statistics (data warehouses only)

#### Phase 3: Testing & Documentation

- [ ] Unit tests (>=80% coverage)
- [ ] Integration tests with golden files
- [ ] User documentation

### For API sources

#### Phase 1: Client & Auth

- [ ] Create `client.py` with API client class
- [ ] Implement authentication (OAuth2/API key/token)
- [ ] Implement pagination and rate limiting
- [ ] Add Pydantic response models

#### Phase 2: Core Extraction

- [ ] Create `config.py` with API config
- [ ] Create `source.py` with primary entity extraction
- [ ] Register in setup.py entry points
- [ ] Verify basic extraction works

#### Phase 3: Additional Features

- [ ] Container hierarchy (workspaces/projects/folders)
- [ ] Lineage (dashboard-to-dataset, job-to-dataset, etc.)
- [ ] Ownership and tags (if applicable)

#### Phase 4: Testing & Documentation

- [ ] Unit tests (>=80% coverage) with mocked API responses
- [ ] Integration tests with golden files
- [ ] User documentation

### For NoSQL sources

#### Phase 1: Connection & Schema Inference

- [ ] Create `config.py` with connection config + schema inference settings
- [ ] Implement schema inference by document sampling
- [ ] Create `source.py` with collection/table extraction

#### Phase 2: Core Extraction

- [ ] Register in setup.py entry points
- [ ] Container hierarchy (databases/keyspaces)
- [ ] Verify basic extraction works

#### Phase 3: Testing & Documentation

- [ ] Unit tests (>=80% coverage)
- [ ] Integration tests with golden files
- [ ] User documentation

## Approval

- [ ] User approved this plan on: {{ approval_date }}
- [ ] Approval message: "{{ approval_message }}"
