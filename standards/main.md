# DataHub Source Implementation Reference Guide

This is the detailed reference guide for implementing DataHub connectors. **For the workflow and step-by-step process, see the main CLAUDE.md file.**

## Golden Connector Standards Directory

This directory contains all technical standards for DataHub connector development:

### Core Standards (Applicable to All Connectors)

- **main.md** (this file) - Core architecture, base classes, SDK usage, planning reference
- **patterns.md** - File structure, imports, error handling, code organization
- **testing.md** - Test requirements, anti-patterns, test strategies

### Source-Type-Specific Standards

- **sql.md** - SQL database connector patterns and requirements
- **api.md** - REST/GraphQL API connector patterns and requirements

### Feature-Specific Standards

- **lineage.md** - Lineage extraction strategies and SqlParsingAggregator usage
- **containers.md** - Container hierarchy patterns (Database → Schema → Table)
- **performance.md** - Memory optimization and performance patterns

### Publishing Standards

- **registration.md** - Documentation requirements and connector registration
- **platform_registration.md** - Platform icons, branding, and setup

### Subdirectories

- **source_types/** - Source-specific patterns organized by platform type (BI tools, data warehouses, ML platforms, streaming, etc.)

---

## Table of Contents

1. [Source Planning Reference](#source-planning-reference) - Detailed planning guidance
2. [Configuration Best Practices](#configuration-best-practices) - How to design consistent, maintainable configurations
3. [Source Type Selection](#source-type-selection) - Reference for categorizing sources
4. [Implementation Guides](#implementation-guides) - Links to specific implementation guides

---

## Source Planning Reference

This section provides detailed guidance for planning your source implementation. Reference these sections as needed during the planning phase outlined in CLAUDE.md.

### Step 1: Research Your Source System

Before writing any code, gather information about your source system:

#### 1.1 Understand the Source's Architecture

- **What type of system is it?** (Database, BI tool, data lake, ML platform, etc.)
- **How does it expose metadata?** (SQL queries, REST API, GraphQL API, SDK)
- **What authentication methods are supported?** (API keys, OAuth, basic auth, service accounts)
- **Does it have API rate limits?** (Document limits for planning pagination)
- **What are the key concepts?** (Tables/Views, Dashboards/Charts, Models/Experiments, etc.)

#### 1.2 Document Metadata Availability

Create a checklist of what metadata is available:

- [ ] **Basic entities** - Tables, dashboards, models, etc.
- [ ] **Schema information** - Column names, types, descriptions
- [ ] **Organizational structure** - Databases/schemas, workspaces/projects, folders
- [ ] **Ownership** - Creators, owners, last modified by
- [ ] **Tags/labels** - Custom tags, classifications
- [ ] **Documentation** - Descriptions, comments, external docs links
- [ ] **Access control** - Permissions, roles, groups
- [ ] **Usage statistics** - Query counts, view counts, user access patterns
- [ ] **Audit logs** - Query history, access logs, change logs
- [ ] **Lineage information** - Dependencies, view definitions, SQL queries

#### 1.3 Review Official Documentation

Read the source system's API documentation:

- **API endpoints** - List available endpoints for metadata extraction
- **Authentication** - Document auth flow and credentials needed
- **Pagination** - Note pagination mechanism (offset/limit, cursor-based, page-based)
- **Rate limits** - Document request limits and throttling behavior
- **Permissions required** - List minimum permissions needed for metadata extraction

**Example** (Snowflake planning):

```
✅ Tables/Views: INFORMATION_SCHEMA.TABLES
✅ Columns: INFORMATION_SCHEMA.COLUMNS
✅ View SQL: GET_DDL('VIEW', <view_name>)
✅ Lineage: SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES (view-to-table)
✅ Usage: SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY (requires Enterprise Edition)
✅ Audit: SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY (requires Enterprise Edition)
⚠️ Limitation: ACCESS_HISTORY only available in Enterprise+ editions
```

---

### Step 2: Find Similar Existing Sources

Look at existing DataHub sources that are similar to your target system.

#### 2.1 Explore the DataHub Source Directory

**Location**: `src/datahub/ingestion/source/` in the DataHub repository

#### 2.2 Recommended Reference Sources by Category

| Your Source Type   | Study These DataHub Sources   | Key Files to Review                                                                              |
| ------------------ | ----------------------------- | ------------------------------------------------------------------------------------------------ |
| **Data Warehouse** | Snowflake, BigQuery, Redshift | `snowflake/snowflake_v2.py`<br>`bigquery_v2/bigquery.py`<br>`*_lineage_v2.py`<br>`*_usage_v2.py` |
| **SQL Database**   | PostgreSQL, MySQL, Oracle     | `sql/sql_common.py`<br>`postgres.py`<br>`mysql/mysql_source.py`                                  |
| **BI Tool**        | Tableau, Looker, Power BI     | `tableau/tableau.py`<br>`looker/looker_source.py`<br>`powerbi/`                                  |
| **Data Lake**      | S3, GCS, Azure ADLS           | `s3/`<br>`gcs/`<br>`azure/adls_gen2.py`                                                          |
| **ML Platform**    | MLflow, SageMaker             | `mlflow.py`<br>`sagemaker/`                                                                      |
| **Orchestration**  | Airflow, Dagster              | `airflow/`<br>`dagster/`                                                                         |
| **Streaming**      | Kafka, Pulsar                 | `kafka/`<br>`pulsar/`                                                                            |
| **Query Engine**   | Dremio, Trino, Presto         | `dremio/`<br>`trino/`<br>`presto/`                                                               |

#### 2.3 What to Look For in Reference Sources

When reviewing similar sources, note:

1. **Configuration structure** (`*_config.py`)
   - How they structure connection config vs source config
   - What filtering options they provide (patterns, allow/deny lists)
   - What feature flags they expose (lineage, usage, profiling)

2. **Entity type mapping** (`*_schema_gen.py` or main source file)
   - How they map source concepts to DataHub entities
   - What subtypes they use
   - How they handle containers (databases, schemas, projects)

3. **Lineage extraction** (`*_lineage*.py`)
   - Where they get lineage from (audit logs, view definitions, system tables)
   - How they parse SQL (if applicable)
   - How they resolve table references to URNs

4. **Usage extraction** (`*_usage*.py`)
   - What audit logs or query history they use
   - How they aggregate statistics
   - What time windows they support

5. **API/SQL client** (`*_client.py` or embedded in main file)
   - How they structure API client classes
   - Retry logic and error handling patterns
   - Pagination implementation

---

### Step 3: Categorize Your Source

Based on your research, categorize your source to determine the implementation approach.

#### 3.1 Primary Categorization: SQL vs API

**Choose ONE**:

- **SQL-Based** → Use [SQL Sources Guide](sql.md)
  - Source has JDBC/ODBC interface
  - Metadata available via SQL queries (INFORMATION_SCHEMA, system tables)
  - Examples: PostgreSQL, Snowflake, BigQuery, Redshift

- **API-Based** → Use [API-Based Sources Guide](api.md)
  - Source exposes REST or GraphQL API
  - No SQL interface or SQL doesn't provide needed metadata
  - Examples: Tableau, Looker, S3, MLflow, Kafka

#### 3.2 Secondary Categorization: Source Type

See [Source Type Selection](#source-type-selection) below for detailed categorization and what entities to extract.

---

### Step 4: Identify Entity Types and Subtypes

Map your source system's concepts to DataHub entity types.

#### 4.1 Review Standard Entity Types

**Location**: `src/datahub/ingestion/source/common/subtypes.py`

**Core Entity Types in DataHub**:

| DataHub Entity     | Use For                                        | Standard Subtypes                                                     |
| ------------------ | ---------------------------------------------- | --------------------------------------------------------------------- |
| **Dataset**        | Tables, views, topics, files, collections      | `TABLE`, `VIEW`, `TOPIC`, `EXTERNAL_TABLE`, `SHARDED_TABLE`, `STREAM` |
| **Container**      | Databases, schemas, projects, folders, buckets | `DATABASE`, `SCHEMA`, `PROJECT`, `FOLDER`, `CATALOG`, `BUCKET`        |
| **Dashboard**      | BI dashboards, reports                         | `DASHBOARD`                                                           |
| **Chart**          | Individual visualizations                      | `CHART`, `LOOKER_LOOK`                                                |
| **DataFlow**       | Pipelines, DAGs, workflows                     | `AIRFLOW_DAG`, `DAGSTER_PIPELINE`                                     |
| **DataJob**        | Tasks, pipeline steps                          | `AIRFLOW_TASK`, `DAGSTER_OP`                                          |
| **MLModel**        | ML model versions                              | `ML_MODEL`                                                            |
| **MLModelGroup**   | Model registries                               | `MODEL_GROUP`                                                         |
| **MLFeatureTable** | Feature store tables                           | `FEATURE_TABLE`                                                       |
| **MLFeature**      | Individual features                            | `FEATURE`                                                             |
| **CorpUser**       | User accounts                                  | N/A                                                                   |
| **CorpGroup**      | Teams, roles, groups                           | N/A                                                                   |

#### 4.2 Map Your Source Concepts to Entity Types

Create a mapping table:

**Example** (Snowflake):

```
Source Concept          → DataHub Entity    → Subtype
─────────────────────────────────────────────────────────────
Database                → Container         → DATABASE
Schema                  → Container         → SCHEMA
Table                   → Dataset           → TABLE
View                    → Dataset           → VIEW
Materialized View       → Dataset           → VIEW (with custom property)
Stream                  → Dataset           → SNOWFLAKE_STREAM
Dynamic Table           → Dataset           → DYNAMIC_TABLE
External Table          → Dataset           → EXTERNAL_TABLE
Stage                   → (Skip - not core metadata)
```

**Example** (Looker):

```
Source Concept          → DataHub Entity    → Subtype
─────────────────────────────────────────────────────────────
Model                   → Container         → LOOKML_MODEL
Explore                 → Dataset           → LOOKER_EXPLORE
Look                    → Chart             → LOOKER_LOOK
Dashboard               → Dashboard         → DASHBOARD
Folder                  → Container         → LOOKER_FOLDER
```

#### 4.3 Check for Reusable Subtypes

**Before creating new subtypes**, check if existing ones fit:

```python
# Standard Dataset Subtypes (from subtypes.py)
class DatasetSubTypes(StrEnum):
    TABLE = "Table"
    VIEW = "View"
    TOPIC = "Topic"
    EXTERNAL_TABLE = "External Table"
    SHARDED_TABLE = "Sharded Table"
    DYNAMIC_TABLE = "Dynamic Table"
    SNOWFLAKE_STREAM = "Snowflake Stream"
    # ... more

# Standard Container Subtypes
class DatasetContainerSubTypes(StrEnum):
    DATABASE = "Database"
    SCHEMA = "Schema"
    CATALOG = "Catalog"
    BIGQUERY_PROJECT = "Project"
    BIGQUERY_DATASET = "Dataset"
    S3_BUCKET = "S3 bucket"
    # ... more
```

**When to create new subtypes**:

- ✅ Your source has a concept that's fundamentally different from existing subtypes
- ✅ The subtype will be useful for filtering/searching in DataHub UI
- ❌ Don't create subtypes for minor variations (use custom properties instead)

#### 4.4 Plan Subtype Usage

Subtypes are **additive**. An entity can have multiple subtypes:

```python
# Example: BigQuery external sharded table
sub_types = [
    DatasetSubTypes.SHARDED_TABLE,  # It's sharded
    DatasetSubTypes.EXTERNAL_TABLE, # It's external
    DatasetSubTypes.TABLE,          # It's a table (base type)
]
```

---

### Step 5: Plan Lineage Extraction

Lineage is one of the most valuable features. Plan how you'll extract it.

#### 5.1 Identify Lineage Sources

**Priority order** (implement in this order for best results):

1. **Audit Logs / Query History** (⭐ BEST - shows actual usage)
   - Pros: Most accurate, captures real queries, includes column-level lineage
   - Cons: Requires permissions, may have data retention limits
   - Examples:
     - Snowflake: `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` + `ACCESS_HISTORY`
     - BigQuery: Cloud Logging API + `INFORMATION_SCHEMA.JOBS_BY_PROJECT`
     - Redshift: `SYS_QUERY_HISTORY`, `STL_QUERY`

2. **View Definitions + SQL Parsing** (⭐ GOOD - standard approach)
   - Pros: Available in most SQL systems, no special permissions
   - Cons: Only captures lineage for views, not ad-hoc queries
   - Implementation: Extract view SQL → parse with `sqlglot_lineage()` → extract table references
   - Examples:
     - Snowflake: `GET_DDL('VIEW', view_name)`
     - PostgreSQL: `pg_views.definition`
     - Looker: Parse LookML SQL definitions

3. **System Dependency Tables** (⚠️ FALLBACK - limited)
   - Pros: Built-in, no parsing needed
   - Cons: Often incomplete, view-level only
   - Examples:
     - Snowflake: `ACCOUNT_USAGE.OBJECT_DEPENDENCIES`
     - SQL Server: `sys.sql_expression_dependencies`

#### 5.2 Document Lineage Capabilities and Limitations

Create a lineage capabilities matrix:

**Example** (Snowflake):

```
Lineage Type              | Available? | Source                          | Limitations
──────────────────────────────────────────────────────────────────────────────────────────
Table → View (via SQL)    | ✅ Yes     | View DDL + SQL parsing          | None
View → Table (query logs) | ⚠️ Partial | ACCESS_HISTORY                  | Enterprise Edition only
S3 → Table (COPY)         | ✅ Yes     | COPY_HISTORY                    | Last 14 days only
Column-level              | ✅ Yes     | Query parsing                   | Requires query text
Pipeline → Table          | ❌ No      | Not available                   | N/A
```

#### 5.3 SQL Parsing Pattern

**⚠️ IMPORTANT**: Use `SqlParsingAggregator` instead of direct `sqlglot_lineage` calls.

`SqlParsingAggregator` is the **recommended approach** for SQL parsing and lineage extraction in DataHub. It provides:

- **Session management** for temp table tracking
- **Multiple input formats** (observed queries, preparsed queries, view definitions, known lineage)
- **Automatic metadata generation** (lineage, queries, operations, usage)
- **File-backed storage** for large-scale processing
- **Deduplication** via query fingerprinting

**Standard pattern:**

```python
from datahub.sql_parsing.sql_parsing_aggregator import SqlParsingAggregator, ObservedQuery

# Initialize aggregator
aggregator = SqlParsingAggregator(
    platform="snowflake",
    platform_instance=config.platform_instance,
    env=config.env,
    generate_lineage=True,
    generate_queries=True,
    generate_usage_statistics=False,
    generate_operations=False,
)

# Add queries from various sources
for query in query_log:
    aggregator.add_observed_query(
        ObservedQuery(
            query=query.text,
            session_id=query.session_id,
            timestamp=query.timestamp,
            user=query.user_urn,
            default_db=query.database,
            default_schema=query.schema,
        )
    )

# Add view definitions
aggregator.add_view_definition(
    view_urn=view_urn,
    view_definition=view_sql,
    default_db="my_database",
    default_schema="public"
)

# Generate all metadata (lineage, queries, usage, operations)
for mcp in aggregator.gen_metadata():
    yield MetadataWorkUnit(id=..., mcp=mcp)
```

**Reference**: See full SqlParsingAggregator guide in [lineage.md](lineage.md#using-sqlparsingaggregator)

---

### Step 6: Plan Usage and Audit Log Extraction

Usage statistics show how data is being used. Plan your approach.

#### 6.1 Identify Usage Data Sources

**Common sources**:

1. **Query Logs** (for databases/warehouses)
   - Snowflake: `QUERY_HISTORY` view
   - BigQuery: `INFORMATION_SCHEMA.JOBS_BY_*`
   - Redshift: `STL_QUERY`, `SVL_STATEMENTTEXT`

2. **Access Logs** (for APIs/BI tools)
   - Tableau: Usage REST API endpoints
   - Looker: `query` API + dashboard access logs
   - S3: CloudTrail events

3. **Audit Logs** (for operations tracking)
   - BigQuery: Cloud Audit Logs (INSERT/UPDATE/DELETE operations)
   - Snowflake: `QUERY_HISTORY` (operation type field)

#### 6.2 Define Usage Metrics to Extract

**Standard usage metrics**:

- **Read counts** - Number of SELECT queries per table
- **Write counts** - Number of INSERT/UPDATE/DELETE operations
- **Unique users** - Count of distinct users accessing the entity
- **Query counts** - Total queries executed
- **Top users** - Most active users by query count
- **Field-level usage** - Column-level access tracking (advanced)

#### 6.3 Document Operation Type Mapping

Map source operations to DataHub operation types:

```python
# Standard pattern (from Snowflake/BigQuery sources)
OPERATION_STATEMENT_TYPES = {
    "INSERT": OperationTypeClass.INSERT,
    "UPDATE": OperationTypeClass.UPDATE,
    "DELETE": OperationTypeClass.DELETE,
    "CREATE": OperationTypeClass.CREATE,
    "ALTER": OperationTypeClass.ALTER,
    "DROP": OperationTypeClass.DROP,
    "MERGE": OperationTypeClass.CUSTOM,
    "COPY": OperationTypeClass.CUSTOM,
}
```

#### 6.4 Plan Time Windows

Define configurable time windows for usage extraction:

```python
# Standard pattern
usage_lookback_days: int = Field(
    default=7,
    description="Number of days to look back for usage statistics"
)
```

---

### Step 7: Create Planning Document

Document your planning decisions before coding.

#### 7.1 Create a Planning Checklist

**File**: `<your_source>_PLANNING.md`

```markdown
# [Source Name] DataHub Connector Planning

## Source Information

- **Type**: [SQL Database / API-Based / etc.]
- **API/Interface**: [REST API / JDBC / GraphQL]
- **Authentication**: [API Key / OAuth / Basic Auth]
- **Documentation**: [Link to official API docs]

## Entity Mapping

| Source Concept | DataHub Entity | Subtype | Notes |
| -------------- | -------------- | ------- | ----- |
| ...            | ...            | ...     | ...   |

## Metadata Extraction Plan

- [ ] Basic metadata (names, descriptions)
- [ ] Schema information (columns, types)
- [ ] Containers (databases, schemas, folders)
- [ ] Ownership information
- [ ] Tags/labels
- [ ] Custom properties
- [ ] Domains
- [ ] Glossary terms

## Lineage Extraction Plan

- **Method**: [Audit logs / View SQL parsing / System tables]
- **Source**: [Specific API/table name]
- **Limitations**: [Document any limitations]
- **Column-level**: [Yes/No]

## Usage Extraction Plan

- **Method**: [Query logs / Access logs]
- **Metrics**: [Read counts, write counts, users]
- **Lookback**: [7 days / 30 days / configurable]
- **Limitations**: [Document any limitations]

## Audit Log Investigation

- **Available**: [Yes/No]
- **Location**: [API endpoint / system table]
- **Permissions Required**: [List required permissions]
- **Data Retention**: [How long logs are kept]
- **Format**: [JSON / Table / etc.]

## Reference Sources

- Similar DataHub source: [e.g., snowflake, looker]
- Key files reviewed: [List file paths]
- Patterns to reuse: [List specific patterns]

## Implementation Notes

- **Challenges**: [List anticipated challenges]
- **Dependencies**: [External libraries needed]
- **Testing Strategy**: [How you'll test this]
```

---

### Step 8: Review and Validate Plan

Before starting implementation:

1. **Review with a colleague** - Get feedback on your entity mapping
2. **Check for similar PRs** - Search DataHub GitHub for similar sources
3. **Validate API access** - Ensure you can access all needed endpoints/tables
4. **Test authentication** - Verify credentials and permissions work
5. **Confirm data availability** - Run sample queries to validate metadata exists

---

### Planning Complete → Start Implementation

Once you've completed steps 1-8, you're ready to implement:

1. Choose implementation guide: [SQL](sql.md) or [API](api.md)
2. Follow the step-by-step implementation instructions
3. Refer back to your planning document as you code
4. Update your planning document if you discover new information

---

## Configuration Best Practices

**⚠️ CRITICAL**: Configuration design is crucial for maintainability and consistency across DataHub sources. Follow these patterns to avoid config bloat and ensure usability.

### Why Configuration Matters

- **Consistency**: Users expect similar config options across sources
- **Discoverability**: Well-named config makes features discoverable
- **Maintainability**: Clean config reduces technical debt
- **Avoid Bloat**: Too many unused options confuse users and increase maintenance burden

### Rule #1: Justify Every Config Option

**Before adding a new config field**, ask:

1. ✅ **Is it essential?** - Does it control a core feature or connection parameter?
2. ✅ **Is it reusable?** - Will most users of this source need this option?
3. ✅ **Does a standard pattern exist?** - Check if other sources have similar config (use same name!)
4. ❌ **Is it a one-off edge case?** - Consider if it's too specific for general use
5. ❌ **Can it be auto-detected?** - Prefer smart defaults over user configuration
6. ❌ **Is it for debugging only?** - Use `HiddenFromDocs` or remove from public API

**Config bloat warning signs**:

- Source has 40+ top-level config fields
- Multiple ways to do the same thing (`use_v2`, `enable_new_method`, etc.)
- Fields that are never or rarely used
- Fields with complex interdependencies

---

### Configuration Structure Pattern

**Standard Hierarchy** (use composition through inheritance):

```python
# 1. Connection Config (separate file: <source>_connection.py)
class MySourceConnectionConfig(ConfigModel):
    """Platform-specific connection details"""
    # Authentication
    api_url: str
    api_key: Optional[pydantic.SecretStr] = None
    username: Optional[str] = None
    password: Optional[pydantic.SecretStr] = None

    # Connection options
    timeout_seconds: int = 30
    max_retries: int = 3

# 2. Filter Config (in <source>_config.py)
class MySourceFilterConfig(ConfigModel):
    """Data filtering patterns"""
    database_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
    schema_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
    table_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()

# 3. Main Source Config (composition)
class MySourceConfig(
    StatefulIngestionConfigBase,     # State management
    PlatformInstanceConfigMixin,     # Multi-instance support
    EnvConfigMixin,                  # Environment classification
    ClassificationSourceConfigMixin, # PII detection (if applicable)
):
    # Connection
    connection: MySourceConnectionConfig

    # Filters
    database_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
    schema_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()

    # Feature toggles
    include_table_lineage: bool = True
    include_usage_stats: bool = False
    include_view_definitions: bool = True

    # Advanced options (with smart defaults)
    max_workers: int = Field(
        default_factory=lambda: os.cpu_count() or 10,
        description="Max parallelism for extraction"
    )
```

---

### Standard Mixins - When to Use Them

**Location**: `src/datahub/configuration/source_common.py`

| Mixin                               | When to Use                            | What It Provides                                              |
| ----------------------------------- | -------------------------------------- | ------------------------------------------------------------- |
| **PlatformInstanceConfigMixin**     | **ALWAYS** (unless single-tenant only) | `platform_instance` field for multi-instance support          |
| **EnvConfigMixin**                  | **ALWAYS**                             | `env` field (PROD/DEV/STAGING) for environment classification |
| **LowerCaseDatasetUrnConfigMixin**  | SQL/data sources                       | `convert_urns_to_lowercase` for URN normalization             |
| **ClassificationSourceConfigMixin** | Sources with column data               | PII/sensitivity detection configuration                       |
| **StatefulIngestionConfigBase**     | Sources supporting deletion detection  | `stateful_ingestion` configuration                            |
| **Stateful\*ConfigMixin**           | Advanced state tracking                | Lineage/usage/profiling state management                      |

**Example** (minimal API source):

```python
class MyAPISourceConfig(
    StatefulIngestionConfigBase,     # For deletion detection
    PlatformInstanceConfigMixin,     # For multi-instance
    EnvConfigMixin,                  # For environment
):
    connection: MyAPIConnectionConfig
    dashboard_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
    extract_usage_stats: bool = False
```

**Example** (full SQL source):

```python
class MySQLSourceConfig(
    SQLCommonConfig,                    # SQL-specific common config
    StatefulLineageConfigMixin,         # Lineage state
    StatefulUsageConfigMixin,           # Usage state
    StatefulProfilingConfigMixin,       # Profiling state
    ClassificationSourceConfigMixin,    # PII detection
    PlatformInstanceConfigMixin,        # Multi-instance
    EnvConfigMixin,                     # Environment
    LowerCaseDatasetUrnConfigMixin,     # URN normalization
):
    # ... source-specific config
```

---

### Config Field Naming Conventions

Follow these patterns for consistency across all sources:

#### Feature Toggles

| Pattern         | Use For                                | Examples                                                                                                   |
| --------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **`include_*`** | Toggle ingestion of entity types       | `include_table_lineage`<br>`include_usage_stats`<br>`include_view_definitions`<br>`include_column_lineage` |
| **`extract_*`** | Extract metadata from external systems | `extract_tags`<br>`extract_owners`<br>`extract_usage_history`                                              |
| **`enable_*`**  | Enable experimental/advanced features  | `enable_stateful_lineage_ingestion`<br>`enable_stateful_usage_ingestion`                                   |
| **`use_*`**     | Choose between strategies              | `use_queries_v2`<br>`use_file_backed_cache`                                                                |

**Examples from Snowflake**:

```python
include_table_lineage: bool = True
include_column_lineage: bool = True
include_usage_stats: bool = True
include_view_definitions: bool = True
extract_tags: TagOption = TagOption.with_lineage
use_queries_v2: bool = True
```

#### Filter Fields

**Pattern**: `{entity_type}_pattern: AllowDenyPattern`

```python
# Standard patterns (use these names across sources)
database_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
schema_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
table_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
view_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()

# Platform-specific patterns (only when needed)
stream_pattern: AllowDenyPattern  # Snowflake streams
procedure_pattern: AllowDenyPattern  # Snowflake procedures
dashboard_pattern: AllowDenyPattern  # BI tools
chart_pattern: AllowDenyPattern  # BI tools
```

**Filter naming rules**:

- ✅ Use `_pattern` suffix for AllowDenyPattern
- ✅ Use singular form (`table_pattern`, not `tables_pattern`)
- ✅ Use common names where possible (`database`, `schema`, `table`)
- ❌ Don't invent new names for standard entities

#### Time Windows

**🔴 CRITICAL**: ALWAYS use DataHub's standard time window classes for usage and lineage extraction.

**✅ CORRECT - Use BaseTimeWindowConfig or BaseUsageConfig**:

```python
from datahub.configuration.time_window_config import BaseTimeWindowConfig
from datahub.ingestion.source.usage.usage_common import BaseUsageConfig

# For usage extraction (includes time window + usage-specific config)
class MySourceUsageConfig(BaseUsageConfig):
    # Automatically inherits:
    # - start_time: datetime or relative string (e.g., "-7 days")
    # - end_time: datetime (default: now)
    # - bucket_duration: BucketDuration (DAY or HOUR)
    # - top_n_queries: int (default: 10)
    # - user_email_pattern: AllowDenyPattern
    # - include_operational_stats: bool

    # Add source-specific fields
    enabled: bool = Field(
        default=False,
        description="Enable usage extraction"
    )

# For lineage extraction from query logs (time window only)
class MySourceQueryLogConfig(BaseTimeWindowConfig):
    # Automatically inherits:
    # - start_time: datetime or relative string
    # - end_time: datetime
    # - bucket_duration: BucketDuration

    enabled: bool = Field(
        default=False,
        description="Enable query log lineage extraction"
    )
```

**❌ WRONG - Do NOT create custom time window fields**:

```python
# ❌ DON'T DO THIS - creates inconsistency with other sources
usage_lookback_days: int = Field(
    default=7,
    description="Number of days to look back for usage statistics"
)

# ❌ DON'T DO THIS - reinvents the wheel
usage_start_date: str = Field(
    default=None,
    description="Start date for usage extraction"
)
```

**Why BaseTimeWindowConfig is required:**

- ✅ Consistent across ALL DataHub sources (Snowflake, BigQuery, Redshift, etc.)
- ✅ Supports both relative time (`"-7 days"`) and absolute timestamps
- ✅ Automatic validation and timezone handling
- ✅ Time bucketing (DAY vs HOUR aggregation)
- ✅ Integration with stateful ingestion via `StatefulTimeWindowConfigMixin`
- ✅ Standard helper methods like `.buckets()` and `.majority_buckets()`

**When to use each:**

- **BaseUsageConfig**: For usage statistics extraction (query logs, access logs)
- **BaseTimeWindowConfig**: For lineage extraction from query logs (without usage stats)
- **StatefulTimeWindowConfigMixin**: Add to main config for stateful time window tracking

---

### Field Validation Patterns

#### Field-Level Validators

Use `@field_validator` for single-field validation:

```python
from pydantic import field_validator

class MySourceConfig(ConfigModel):
    api_url: str
    include_column_lineage: bool = True
    include_table_lineage: bool = True

    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate and normalize API URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("API URL must start with http:// or https://")
        return v.rstrip("/")  # Remove trailing slash

    @field_validator("include_column_lineage")
    @classmethod
    def validate_column_lineage_dependency(cls, v: bool, info: ValidationInfo) -> bool:
        """Column lineage requires table lineage"""
        if v and not info.data.get("include_table_lineage"):
            raise ValueError(
                "include_table_lineage must be True for "
                "include_column_lineage to be set."
            )
        return v
```

#### Model-Level Validators

Use `@model_validator` for cross-field validation:

```python
from pydantic import model_validator

class MySourceConfig(ConfigModel):
    include_usage_stats: bool = False
    usage_start_time: Optional[datetime] = None
    usage_end_time: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_usage_config(self) -> "MySourceConfig":
        """Validate usage configuration consistency"""
        if self.include_usage_stats:
            if not self.usage_start_time or not self.usage_end_time:
                raise ValueError(
                    "usage_start_time and usage_end_time must be set "
                    "when include_usage_stats is True"
                )
            if self.usage_end_time <= self.usage_start_time:
                raise ValueError(
                    "usage_end_time must be after usage_start_time"
                )
        return self
```

#### Backwards Compatibility

Handle deprecated/renamed fields gracefully:

```python
from datahub.configuration.pydantic_field_deprecation import (
    pydantic_removed_field,
    pydantic_renamed_field,
)

class MySourceConfig(ConfigModel):
    # Remove deprecated field
    _removed_old_option = pydantic_removed_field("old_option")

    # Rename field (old_name → new_name)
    _rename_project = pydantic_renamed_field("project_id", "project_ids")

    # Current field
    project_ids: List[str] = []

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_project_id(cls, values: Dict) -> Dict:
        """Convert legacy project_id to project_ids"""
        values = deepcopy(values)
        project_id = values.pop("project_id", None)
        project_ids = values.get("project_ids")

        if not project_ids and project_id:
            values["project_ids"] = [project_id]
            logger.warning(
                "project_id is deprecated, use project_ids instead"
            )
        return values
```

---

### Smart Defaults

Provide sensible defaults to minimize required configuration:

```python
from typing import Optional
import os
from datetime import datetime, timezone

class MySourceConfig(ConfigModel):
    # Dynamic defaults
    max_workers: int = Field(
        default_factory=lambda: os.cpu_count() or 10,
        description="Max parallelism. Defaults to CPU count or 10"
    )

    end_time: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="End time for usage extraction. Defaults to now"
    )

    # Permissive defaults
    database_pattern: AllowDenyPattern = Field(
        default_factory=AllowDenyPattern.allow_all,
        description="Regex patterns to filter databases"
    )

    # Safe defaults (opt-in for expensive operations)
    include_usage_stats: bool = Field(
        default=False,
        description="Extract usage statistics (requires additional permissions)"
    )

    include_profiling: bool = Field(
        default=False,
        description="Run data profiling (can be slow on large tables)"
    )

    # Feature flags (opt-in for new features)
    use_queries_v2: bool = Field(
        default=False,
        description="Use new query extraction method (experimental)"
    )
```

---

### Hidden and Debug Options

Use `HiddenFromDocs` for internal/debug options:

```python
from typing import Optional
from datahub.configuration.common import HiddenFromDocs

class MySourceConfig(ConfigModel):
    # Public options
    api_url: str = Field(description="API endpoint URL")
    api_key: pydantic.SecretStr = Field(description="API authentication key")

    # Hidden from documentation (internal use)
    debug_include_full_payloads: HiddenFromDocs[bool] = Field(
        default=False,
        description="[DEBUG] Include full API response payloads in logs"
    )

    _cache_ttl_seconds: HiddenFromDocs[int] = Field(
        default=3600,
        description="[INTERNAL] Cache TTL for API responses"
    )
```

**When to hide options**:

- ✅ Debugging flags that shouldn't be used in production
- ✅ Internal implementation details
- ✅ Experimental options not ready for public use
- ❌ Don't hide commonly needed options
- ❌ Don't use as excuse for poor design

---

### Avoiding Config Bloat

**Warning Signs of Config Bloat**:

1. **Too many top-level fields** (>40 fields)
   - Solution: Group related settings into nested configs

2. **Multiple strategies for same feature**

   ```python
   # BAD: Multiple ways to do lineage
   use_legacy_lineage: bool
   use_queries_v2: bool
   lineage_strategy: str  # "legacy", "v2", "experimental"

   # GOOD: Single strategy selector
   lineage_method: LineageMethod = LineageMethod.QUERY_LOG  # Enum
   ```

3. **Unused feature flags**

   ```python
   # BAD: Feature that was never finished
   include_experimental_metadata: bool = False  # Never implemented

   # GOOD: Remove unimplemented features
   ```

4. **Over-granular control**

   ```python
   # BAD: Too many extraction toggles
   extract_table_comments: bool = True
   extract_column_comments: bool = True
   extract_view_comments: bool = True
   extract_schema_comments: bool = True

   # GOOD: Single toggle
   extract_comments: bool = True
   ```

#### Refactoring Config Bloat

**Group related settings**:

```python
# BEFORE: Flat config (too many fields)
class MySourceConfig(ConfigModel):
    include_usage_stats: bool
    usage_lookback_days: int
    usage_min_query_count: int
    usage_exclude_system_users: bool
    usage_bucket_duration: str
    # ... 30 more fields

# AFTER: Nested config
class UsageConfig(ConfigModel):
    enabled: bool = False
    lookback_days: int = 7
    min_query_count: int = 1
    exclude_system_users: bool = True
    bucket_duration: BucketDuration = BucketDuration.DAY

class MySourceConfig(ConfigModel):
    usage: UsageConfig = UsageConfig()
    # ... other configs
```

---

### Pydantic v2 Usage

**⚠️ CRITICAL**: DataHub uses Pydantic v2. **Never use deprecated v1 methods**.

#### Migration Quick Reference

| **Pydantic v1 (❌ DEPRECATED)** | **Pydantic v2 (✅ USE THIS)**             |
| ------------------------------- | ----------------------------------------- |
| `Model.parse_obj(dict)`         | `Model.model_validate(dict)`              |
| `model.dict()`                  | `model.model_dump()`                      |
| `model.json()`                  | `model.model_dump_json()`                 |
| `@validator('field')`           | `@field_validator('field', mode='after')` |
| `@root_validator`               | `@model_validator(mode='before/after')`   |
| `class Config:`                 | `model_config = ConfigDict(...)`          |

#### Key Patterns

**Parsing configurations**:

```python
# ✅ Correct - Pydantic v2
config = MyConfig.model_validate(config_dict)

# ❌ Wrong - Pydantic v1 (deprecated)
config = MyConfig.parse_obj(config_dict)
```

**Serializing configurations**:

```python
# ✅ Correct - Pydantic v2
config_dict = my_config.model_dump()
config_dict = my_config.model_dump(exclude_none=True)

# ❌ Wrong - Pydantic v1 (deprecated)
config_dict = my_config.dict()
```

**Model configuration**:

```python
# ✅ Correct - Pydantic v2
from pydantic import BaseModel, ConfigDict

class MyConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

# ❌ Wrong - Pydantic v1 (deprecated)
class MyConfig(BaseModel):
    class Config:
        extra = "forbid"
```

**Field validators**:

```python
# ✅ Correct - Pydantic v2
from pydantic import field_validator, ValidationInfo

@field_validator("timeout", mode="after")
@classmethod
def validate_timeout(cls, v: int) -> int:
    if v <= 0:
        raise ValueError("timeout must be positive")
    return v

# Access other fields
@field_validator("enable_lineage", mode="after")
@classmethod
def validate_lineage(cls, v: bool, info: ValidationInfo) -> bool:
    api_url = info.data.get("api_url", "")
    if v and "v1" in api_url:
        raise ValueError("Lineage requires API v2")
    return v

# ❌ Wrong - Pydantic v1 (deprecated)
@validator('timeout')
def validate_timeout(cls, v):
    return v
```

**Model validators**:

```python
# ✅ Correct - Pydantic v2
from pydantic import model_validator
from typing import Dict, Any

# Before parsing (dict-based)
@model_validator(mode="before")
@classmethod
def apply_defaults(cls, values: Dict[str, Any]) -> Dict[str, Any]:
    if "timeout" not in values and values.get("enable_lineage"):
        values["timeout"] = 60
    return values

# After parsing (instance-based)
@model_validator(mode="after")
def validate_consistency(self) -> Self:
    if self.enable_lineage and self.timeout < 30:
        logger.warning("Lineage may timeout with timeout < 30")
    return self

# ❌ Wrong - Pydantic v1 (deprecated)
@root_validator
def validate_model(cls, values):
    return values
```

**Use DataHub's ConfigModel**:

```python
from datahub.configuration.common import ConfigModel

class MySourceConfig(ConfigModel):
    # ConfigModel already has proper Pydantic v2 setup
    # Just add your fields
    api_url: str = Field(description="API endpoint")
    timeout: int = Field(default=30, description="Timeout in seconds")
```

For complete examples and patterns, see the [Pydantic v2 Patterns section in registration.md](registration.md#j-pydantic-v2-patterns).

---

### Configuration Checklist

Before finalizing your config, verify:

**Required**:

- [ ] All fields have descriptions
- [ ] Sensitive fields use `pydantic.SecretStr`
- [ ] Filters use `AllowDenyPattern` (not custom regex)
- [ ] Naming follows conventions (`include_*`, `extract_*`, `{entity}_pattern`)
- [ ] Smart defaults are provided
- [ ] Cross-field dependencies are validated
- [ ] Inherit from appropriate mixins (Platform, Env, Stateful)

**Config Justification**:

- [ ] Every config option is essential (not "nice to have")
- [ ] Check similar sources for existing patterns
- [ ] No duplicate ways to configure same feature
- [ ] No unused or half-implemented options
- [ ] Debug options are hidden or removed

**Backwards Compatibility**:

- [ ] Deprecated fields handled with `pydantic_removed_field`
- [ ] Renamed fields handled with `pydantic_renamed_field`
- [ ] Migration warnings logged for users

**Documentation**:

- [ ] Field descriptions include examples where helpful
- [ ] Complex configs have usage examples
- [ ] Limitations documented (e.g., "Enterprise Edition only")

---

### Config Anti-Patterns to Avoid

#### ❌ DON'T: Create Platform-Specific Names for Common Concepts

```python
# BAD: Using platform-specific terminology
redshift_database_name: str
redshift_cluster_id: str

# GOOD: Use standard terminology
database: str
host: str
```

#### ❌ DON'T: Make Everything Configurable

```python
# BAD: Over-engineering configuration
api_retry_initial_backoff_ms: int = 1000
api_retry_backoff_multiplier: float = 2.0
api_retry_max_backoff_ms: int = 32000
api_retry_jitter_ms: int = 100

# GOOD: Sensible default with minimal config
max_retries: int = 3  # Uses exponential backoff internally
```

#### ❌ DON'T: Use Strings for Enums

```python
# BAD: String typing without validation
lineage_mode: str  # User types "query_log" or "view_definitions"?

# GOOD: Use enums
class LineageMode(StrEnum):
    QUERY_LOG = "query_log"
    VIEW_DEFINITIONS = "view_definitions"
    SYSTEM_TABLES = "system_tables"

lineage_mode: LineageMode = LineageMode.QUERY_LOG
```

#### ❌ DON'T: Nest Too Deeply

```python
# BAD: Excessive nesting
config.extraction.lineage.query_log.filters.table_patterns.allow

# GOOD: Flat where possible
config.table_pattern  # AllowDenyPattern handles allow/deny internally
```

---

### Configuration Examples from Well-Designed Sources

**Simple API Source** (Looker):

```python
class LookerSourceConfig(
    StatefulIngestionConfigBase,
    PlatformInstanceConfigMixin,
    EnvConfigMixin,
):
    connection: LookerConnectionConfig
    dashboard_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
    chart_pattern: AllowDenyPattern = AllowDenyPattern.allow_all()
    extract_owners: bool = True
    extract_usage_history: bool = False
    max_threads: int = 10
```

**Clean SQL Source** (Redshift):

```python
class RedshiftConfig(
    SQLCommonConfig,
    StatefulLineageConfigMixin,
    StatefulUsageConfigMixin,
    PlatformInstanceConfigMixin,
    EnvConfigMixin,
):
    database: str
    username: str
    password: pydantic.SecretStr
    host_port: str
    include_views: bool = True
    include_tables: bool = True
    use_lineage_v2: bool = True
```

---

## Source Type Selection

Choose the appropriate guide based on your source system type:

### API-Based Sources

These sources expose metadata through REST/GraphQL APIs:

- **[BI Tools](source_types/bi_tools.md)** - Tableau, Looker, Power BI, Qlik, Metabase, Superset
  - Extract: Dashboards, Charts, Datasets (for lineage), Containers, Users, Tags
  - Lineage: From Custom SQL, LookML, M Query

- **[Data Lakes](source_types/data_lakes.md)** - AWS S3, Google Cloud Storage, Azure Data Lake Storage
  - Extract: Files/objects, Metadata tags, Buckets/containers

- **[Identity Platforms](source_types/identity_platforms.md)** - Okta, Azure AD, Google Workspace
  - Extract: Users, Groups, Group memberships

- **[ML Platforms](source_types/ml_platforms.md)** - MLflow, Weights & Biases, SageMaker, Vertex AI
  - Extract: MLModels, MLModelGroups, MLFeatureTables, Experiments, Training runs

- **[Orchestration Tools](source_types/orchestration_tools.md)** - Airflow, Prefect, Dagster
  - Extract: DataFlows (DAGs), DataJobs (tasks), Lineage from SQL operators

- **[Streaming Platforms](source_types/streaming_platforms.md)** - Kafka, Kinesis, Pulsar
  - Extract: Topics/streams, Schemas, Domains

- **[Product Analytics](source_types/product_analytics.md)** - Snowplow, Amplitude, Mixpanel, Segment
  - Extract: Event streams, Collections, Projects

- **[NoSQL Databases](source_types/nosql_databases.md)** - MongoDB, Cassandra, DynamoDB, Redis, Elasticsearch
  - Extract: Collections/tables, Keyspaces/databases (when using REST APIs)

### SQL-Based Sources

These sources have SQL/JDBC interfaces and traditional database schemas:

- **[Data Warehouses](source_types/data_warehouses.md)** - Snowflake, Redshift, BigQuery, Databricks
  - Extract: Tables, Views, Schemas, Databases, Column metadata, Tags, Lineage from query logs

- **[SQL Databases](source_types/sql_databases.md)** - PostgreSQL, MySQL, Oracle, SQL Server, DB2
  - Extract: Tables, Views, Schemas, Databases, Column metadata, Constraints

- **[Query Engines](source_types/query_engines.md)** - Dremio, Trino, Presto, Hive, Spark SQL
  - Extract: Tables, Views, Virtual datasets, Catalogs, Lineage from view definitions

---

## Implementation Guides

Once you've completed planning and configuration design, use these implementation guides:

### SQL-Based Sources

- **[SQL Sources Guide](sql.md)** - For databases, warehouses, and query engines with SQL interfaces
  - Extends `SQLAlchemySource` or `TwoTierSQLAlchemySource`
  - Query-based metadata extraction
  - Schema introspection patterns

### API-Based Sources

- **[API-Based Sources Guide](api.md)** - For REST/GraphQL APIs
  - Extends `StatefulIngestionSourceBase`
  - HTTP client patterns
  - Pagination and rate limiting

### Specialized Topics

- **[Lineage Extraction](lineage.md)** - Implementing table and column-level lineage
- **[Common Patterns](patterns.md)** - Shared utilities and patterns
- **[Performance](performance.md)** - Performance and memory optimization
- **[Testing](testing.md)** - Unit and integration testing strategies
- **[Registration & Documentation](registration.md)** - Publishing your source

---

## Best Practices Summary

### Configuration

- ✅ Match source system terminology
- ✅ Use `SecretStr` for sensitive data
- ✅ Provide descriptions for all fields
- ✅ Use `AllowDenyPattern` for filtering
- ✅ Inherit from appropriate base config

### Implementation

- ✅ Separate API client from source logic
- ✅ Use structured reporting
- ✅ Implement proper error handling
- ✅ Support stateful ingestion
- ✅ Implement `test_connection()`
- ✅ Add comprehensive docstrings
- ✅ **Use DataHub SDK V2 (MANDATORY for new connectors)** - See dedicated section below

### 🔴 CRITICAL: Use DataHub SDK V2 for All New Connectors

**MANDATORY for new connectors.** DataHub SDK V2 provides a modern, cleaner API for creating metadata entities.

**SDK V2 Location**: https://github.com/datahub-project/datahub/tree/master/metadata-ingestion/src/datahub/sdk

**Why SDK V2 is required:**

1. **Simpler API**: Less boilerplate compared to raw aspect builders
2. **Type Safety**: Better IDE support and compile-time validation
3. **Maintainability**: Easier to read and understand
4. **Future-proof**: New DataHub features will be added to SDK V2 first
5. **Consistency**: All new connectors should follow the same pattern

**When to use SDK V2:**

- ✅ **ALWAYS** when creating a new connector from scratch
- ✅ **ALWAYS** when adding new entity types to a connector
- ⚠️ **OPTIONAL** when making small bug fixes to existing connectors (can keep old approach for consistency within that connector)
- ⚠️ **OPTIONAL** when adding minor features to existing connectors using old approach

**Key SDK V2 classes:**

- `datahub.sdk.Dataset` - For creating dataset (table/view) entities
- `datahub.sdk.Container` - For creating container entities (databases, schemas, projects)
- `datahub.emitter.mcp_builder` - For building MCPs with SDK V2 patterns

**Example: Dataset creation with SDK V2**

**✅ CORRECT - SDK V2 approach:**

```python
from datahub.sdk import Dataset
from datahub.metadata.schema_classes import DatasetPropertiesClass

# Create dataset using SDK V2
dataset = Dataset(
    platform="duckdb",
    name="my_database.my_schema.my_table",
    env="PROD"
)

# Add properties
dataset.properties = DatasetPropertiesClass(
    description="My table description",
    customProperties={"owner": "data-team"}
)

# Emit as MCP
yield dataset.as_workunit()
```

**❌ WRONG - Old approach (don't use for new connectors):**

```python
from datahub.metadata.schema_classes import DatasetSnapshotClass, MetadataChangeEventClass
from datahub.metadata.com.linkedin.pegasus2avro.mxe import MetadataChangeEvent

# Old approach - verbose and error-prone
dataset_snapshot = DatasetSnapshotClass(
    urn=DatasetUrn(
        platform="duckdb",
        name="my_database.my_schema.my_table",
        env="PROD"
    ).urn(),
    aspects=[]
)

dataset_snapshot.aspects.append(
    DatasetPropertiesClass(
        description="My table description",
        customProperties={"owner": "data-team"}
    )
)

mce = MetadataChangeEventClass(proposedSnapshot=dataset_snapshot)
yield MetadataWorkUnit(id=..., mce=mce)
```

**Example: Container creation with SDK V2**

**✅ CORRECT - SDK V2 approach:**

```python
from datahub.sdk import Container
from datahub.emitter.mcp_builder import ContainerKey

# Create container using SDK V2
container = Container(
    key=ContainerKey(
        platform="duckdb",
        instance="prod",
        container_path=["my_database", "my_schema"]
    ),
    name="my_schema",
    description="Schema containing analytics tables",
    sub_type="Schema"
)

yield container.as_workunit()
```

**Verification checklist for new connectors:**

- [ ] I'm using `datahub.sdk.Dataset` instead of `DatasetSnapshotClass`
- [ ] I'm using `datahub.sdk.Container` instead of manually building container MCPs
- [ ] I'm using `.as_workunit()` to emit SDK V2 objects
- [ ] I'm NOT mixing SDK V2 and old approach in the same connector

**If working on existing connector with old approach:**

- Small bug fix → OK to keep old approach for consistency
- Adding new major feature → Consider migrating to SDK V2
- Adding new entity type → Use SDK V2 for new entity type

**DO NOT use old approach for new connectors - code reviews will require SDK V2.**

### Testing

- ✅ Unit tests for configuration
- ✅ Mock external APIs
- ✅ Golden file tests for SQL sources
- ✅ Integration tests with Docker
- ✅ Test filtering and edge cases

### URNs

- ✅ Use consistent naming
- ✅ Match upstream source URNs for lineage
- ✅ Include platform instance for multi-tenant
- ✅ Use typed urn where possible -> https://github.com/datahub-project/datahub/tree/master/metadata-ingestion/src/datahub/utilities/urns

### Performance

- ✅ Use pagination for large result sets
- ✅ Implement request retry logic
- ✅ Add rate limiting
- ✅ Use connection pooling
- ✅ Batch API requests when possible

---

## Getting Help

- Official docs: <https://datahubproject.io/docs/metadata-ingestion>
- Slack: <https://datahubspace.slack.com/>
- GitHub: <https://github.com/datahub-project/datahub>
