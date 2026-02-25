# Writing a New SQL Source

This guide covers implementing SQL database sources using SQLAlchemy.

## When to Use This Pattern

Use SQLAlchemy-based sources when:

- The database has a SQLAlchemy dialect (official or third-party)
- You need standardized metadata extraction (tables, columns, types, constraints)
- You want built-in profiling and classification support
- The database follows standard SQL information_schema patterns

## Architecture Overview

```
SQLAlchemySource (sql_common.py)
    ↓ extends
StatefulIngestionSourceBase + TestableSource
    ↓ provides
- SQLAlchemy engine/inspector management
- Schema/table/view discovery
- Type mapping
- Profiling integration
- Lineage via SQL parsing
- Stateful ingestion & deletion detection
```

## Step-by-Step Implementation

### 1. Create Configuration Class

**Location**: `src/datahub/ingestion/source/<platform>/<platform>.py`

```python
import pydantic
from pydantic import Field
from typing import Optional

from datahub.configuration.common import AllowDenyPattern
from datahub.ingestion.source.sql.sql_config import (
    SQLAlchemyConnectionConfig,
    SQLCommonConfig,
)

class MyDatabaseConnectionConfig(SQLAlchemyConnectionConfig):
    """Connection configuration specific to your database"""

    # Override scheme for your SQLAlchemy dialect
    # Note: The scheme should typically match the standard SQLAlchemy dialect.
    # Only allow customization if multiple drivers are available or commonly used.
    # If the scheme should not be changed, add a note in the description.
    scheme: str = Field(
        default="mydatabase+driver",
        description="SQLAlchemy scheme (e.g., 'postgresql+psycopg2', 'mysql+pymysql'). "
        "This should typically not be changed unless using an alternative driver."
    )

    # Add database-specific connection parameters
    warehouse: Optional[str] = Field(
        default=None,
        description="Warehouse name (if your database has this concept)"
    )

    role: Optional[str] = Field(
        default=None,
        description="Role to use for connection"
    )

    # Authentication options
    auth_mode: str = Field(
        default="password",
        description="Authentication mode: 'password', 'token', etc."
    )

    # ALWAYS use SecretStr for sensitive data
    password: Optional[pydantic.SecretStr] = Field(
        default=None,
        exclude=True,  # Exclude from serialization
        description="Password for authentication"
    )

    token: Optional[pydantic.SecretStr] = Field(
        default=None,
        exclude=True,
        description="Authentication token (alternative to password)"
    )

    def get_sql_alchemy_url(self, database: Optional[str] = None) -> str:
        """Construct SQLAlchemy connection URL"""
        from datahub.ingestion.source.sql.sqlalchemy_uri import make_sqlalchemy_uri

        # Use helper to construct URL
        return make_sqlalchemy_uri(
            scheme=self.scheme,
            username=self.username,
            password=self.password.get_secret_value() if self.password else None,
            at=self.host_port,
            db=database or self.database,
            # Add query parameters
            uri_opts={
                "warehouse": self.warehouse,
                "role": self.role,
            } if self.warehouse or self.role else None,
        )


class MyDatabaseConfig(SQLCommonConfig):
    """Full configuration for your database source"""

    # Connection configuration
    connection: MyDatabaseConnectionConfig = Field(
        description="Connection configuration"
    )

    # Database-specific options
    include_materialized_views: bool = Field(
        default=True,
        description="Whether to ingest materialized views"
    )

    # Multi-database support (if applicable)
    database_pattern: AllowDenyPattern = Field(
        default=AllowDenyPattern.allow_all(),
        description="Regex patterns for databases to filter"
    )

    def get_sql_alchemy_url(self, database: Optional[str] = None) -> str:
        return self.connection.get_sql_alchemy_url(database=database)
```

**Key Configuration Principles**:

- Match terminology of source system (e.g., `warehouse` for Snowflake, not generic `host`)
- Use `SecretStr` for all passwords, tokens, API keys
- Inherit from `SQLCommonConfig` to get filtering, profiling, stateful ingestion
- All fields must have descriptions
- **Scheme Configuration**: The `scheme` field should typically use the default SQLAlchemy dialect. Only allow changes if:
  - Multiple drivers are available (e.g., `postgresql+psycopg2` vs `postgresql+asyncpg`)
  - Alternative drivers are commonly used
  - Document why the scheme might need to be changed
- **System Schema Exclusion**: When excluding system schemas, reference the official database documentation:
  - PostgreSQL: `information_schema`, `pg_catalog` (see PostgreSQL docs)
  - MySQL: `information_schema`, `mysql`, `performance_schema`, `sys` (see MySQL docs)
  - DB2: `SYSCAT`, `SYSIBM`, `SYSSTAT`, `SYSTOOLS` (see IBM DB2 docs)
  - SQL Server: `information_schema`, `sys` (see SQL Server docs)
  - Include a comment in the `schema_pattern` field description with a reference to the documentation

### 2. Add Usage and Query Log Lineage Configuration

**🔴 CRITICAL**: For SQL sources with audit logs, ALWAYS use DataHub's standard time window patterns.

```python
from datahub.ingestion.source.usage.usage_common import BaseUsageConfig
from datahub.configuration.time_window_config import BaseTimeWindowConfig
from pydantic import Field

class MyDatabaseUsageConfig(BaseUsageConfig):
    """
    Usage statistics configuration.

    Extends BaseUsageConfig which provides:
    - start_time, end_time, bucket_duration (from BaseTimeWindowConfig)
    - top_n_queries, user_email_pattern, include_operational_stats
    """

    enabled: bool = Field(
        default=False,
        description="Enable usage extraction from query logs/audit logs"
    )

    # Add database-specific usage fields if needed
    include_read_operational_stats: bool = Field(
        default=True,
        description="Include SELECT query statistics"
    )


class MyDatabaseQueryLogLineageConfig(BaseTimeWindowConfig):
    """
    Query log lineage configuration.

    Extends BaseTimeWindowConfig which provides:
    - start_time, end_time, bucket_duration
    """

    enabled: bool = Field(
        default=False,
        description="Enable lineage extraction from query logs"
    )

    # Query types to extract lineage from
    include_insert_lineage: bool = Field(
        default=True,
        description="Extract lineage from INSERT INTO ... SELECT statements"
    )

    include_ctas_lineage: bool = Field(
        default=True,
        description="Extract lineage from CREATE TABLE AS SELECT statements"
    )

    include_select_lineage: bool = Field(
        default=False,
        description="Extract lineage from SELECT statements (can create many lineage edges)"
    )


# Add to main source config
class MyDatabaseConfig(SQLCommonConfig):
    # ... other config fields ...

    usage: MyDatabaseUsageConfig = Field(
        default_factory=MyDatabaseUsageConfig,
        description="Usage statistics extraction configuration"
    )

    query_log_lineage: MyDatabaseQueryLogLineageConfig = Field(
        default_factory=MyDatabaseQueryLogLineageConfig,
        description="Query log lineage extraction configuration"
    )
```

**❌ ANTI-PATTERN - Do NOT do this:**

```python
# ❌ WRONG - Custom time fields instead of BaseTimeWindowConfig
class MyDatabaseConfig(SQLCommonConfig):
    usage_lookback_days: int = Field(
        default=7,
        description="Days to look back for usage"  # ❌ Inconsistent with other sources
    )

    lineage_lookback_days: int = Field(
        default=7,
        description="Days to look back for lineage"  # ❌ Doesn't support absolute time
    )
```

**Why this matters:**

- Consistency with Snowflake, BigQuery, Redshift, Clickhouse, etc.
- Proper stateful ingestion support
- Standard user experience across all sources

### 3. Implement Source Class

```python
from typing import Iterable, Optional, Dict, Any, List
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import create_engine, inspect

from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.api.decorators import (
    capability,
    config_class,
    platform_name,
    support_status,
)
from datahub.ingestion.api.source import SourceCapability
from datahub.ingestion.api.workunit import MetadataWorkUnit
from datahub.ingestion.source.sql.sql_common import (
    SQLAlchemySource,
    register_custom_type,
)
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
)

# Register custom SQLAlchemy types BEFORE class definition
# Map database-specific types to DataHub schema types
try:
    from sqlalchemy_mydatabase import types as custom_types

    register_custom_type(custom_types.CUSTOMARRAY, ArrayTypeClass)
    register_custom_type(custom_types.CUSTOMJSON, RecordTypeClass)
except ImportError:
    pass


@platform_name("MyDatabase")  # Display name in UI
@config_class(MyDatabaseConfig)  # Links config to source
@support_status(SupportStatus.CERTIFIED)  # or INCUBATING, TESTING
@capability(SourceCapability.PLATFORM_INSTANCE, "Enabled by default")
@capability(SourceCapability.DOMAINS, "Enabled by default")
@capability(SourceCapability.DATA_PROFILING, "Optionally enabled via configuration")
@capability(SourceCapability.LINEAGE_COARSE, "Enabled by default for views via SQL parsing. Note: Specify if audit log lineage is also supported.")
@capability(SourceCapability.LINEAGE_FINE, "Enabled by default for views via SQL parsing. Note: Specify if audit log lineage is also supported.")
@capability(SourceCapability.DELETION_DETECTION, "Enabled via stateful ingestion")
class MyDatabaseSource(SQLAlchemySource):
    """
    Ingests metadata from MyDatabase.

    Extracts:
    - Databases, schemas, tables, views
    - Column schemas and types
    - Table and column descriptions
    - View definitions and lineage
    - Table constraints (primary keys, foreign keys)
    - Profiling and classification (optional)
    """

    def __init__(self, config: MyDatabaseConfig, ctx: PipelineContext):
        super().__init__(config, ctx, self.get_platform())
        self.config: MyDatabaseConfig = config

        # Initialize any database-specific clients or handlers
        # Example: Token refresh manager
        self._token_manager = None
        if config.connection.auth_mode == "token":
            self._token_manager = TokenRefreshManager(config.connection)

    @classmethod
    def create(cls, config_dict: dict, ctx: PipelineContext) -> "MyDatabaseSource":
        config = MyDatabaseConfig.parse_obj(config_dict)
        return cls(config, ctx)

    def get_platform(self) -> str:
        """Return platform identifier for URN generation"""
        return "mydatabase"

    def get_inspectors(self) -> Iterable[Inspector]:
        """
        Create SQLAlchemy inspector(s) for metadata extraction.

        Yield multiple inspectors if you support multi-database ingestion.
        For single-database systems, yield one inspector.
        """
        # For single database
        url = self.config.get_sql_alchemy_url()
        engine = create_engine(url, **self.config.options)

        # Setup connection event listeners if needed
        if self._token_manager:
            self._setup_token_refresh_listener(engine)

        with engine.connect() as conn:
            inspector = inspect(conn)
            yield inspector

        # For multi-database support (like Postgres, SQL Server)
        # Query system tables to get database list
        # for database in self._get_databases(inspector):
        #     if self.config.database_pattern.allowed(database):
        #         db_url = self.config.get_sql_alchemy_url(database=database)
        #         db_engine = create_engine(db_url, **self.config.options)
        #         with db_engine.connect() as conn:
        #             yield inspect(conn)

    def get_identifier(
        self,
        *,
        schema: str,
        entity: str,
        inspector: Inspector,
        **kwargs: Any,
    ) -> str:
        """
        Generate dataset identifier for URN creation.

        Format depends on database hierarchy:
        - 3-tier (database.schema.table): "database.schema.table"
        - 2-tier (database.table): "database.table"

        This MUST match the format users expect to see and query.
        """
        # Three-tier: database.schema.table
        regular = f"{schema}.{entity}"
        if hasattr(inspector, "engine") and inspector.engine.url.database:
            return f"{inspector.engine.url.database}.{regular}"
        return regular

        # Two-tier alternative (for databases without schema concept)
        # return f"{schema}.{entity}"  # schema is actually database name

    def get_db_name(self, inspector: Inspector) -> str:
        """Get current database name from inspector"""
        if hasattr(inspector, "engine"):
            return inspector.engine.url.database or "default"
        return "default"

    # Optional: Override schema discovery
    def get_schema_names(self, inspector: Inspector) -> Iterable[str]:
        """
        Get list of schema names.

        Override if database has non-standard schema discovery.
        Default implementation calls inspector.get_schema_names()
        """
        return inspector.get_schema_names()

    # Optional: Custom table properties
    def get_extra_table_properties(
        self, inspector: Inspector, schema: str, table: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract database-specific table properties.

        These will be added to DatasetProperties.customProperties
        """
        try:
            # Query system tables for custom metadata
            # Reference: Database-specific system catalog documentation
            # Example for PostgreSQL: https://www.postgresql.org/docs/current/infoschema-tables.html
            # Example for MySQL: https://dev.mysql.com/doc/refman/8.0/en/information-schema-tables-table.html
            # Always include a reference to the official documentation for the system table/view you're querying
            result = inspector.bind.execute(f"""
                SELECT
                    table_type,
                    storage_format,
                    compression,
                    location
                FROM information_schema.tables
                WHERE table_schema = '{schema}'
                  AND table_name = '{table}'
            """).fetchone()

            if result:
                return {
                    "table_type": result.table_type,
                    "storage_format": result.storage_format,
                    "compression": result.compression,
                    "location": result.location,
                }
        except Exception as e:
            self.report.report_warning(
                f"{schema}.{table}", f"Failed to get extra properties: {e}"
            )
        return None

    # Optional: View lineage via system tables
    def _get_view_lineage_workunits(
        self, inspector: Inspector, schema: str, view: str
    ) -> Iterable[MetadataWorkUnit]:
        """
        Extract view lineage from database system tables.

        This complements the default SQL parsing lineage extraction.
        Use this when:
        - Database has reliable view dependency metadata
        - SQL parsing doesn't work well for your dialect
        """
        try:
            # Query database-specific dependency tables
            # Reference: Database-specific view dependency documentation
            # Example for PostgreSQL: pg_depend system catalog
            # Example for DB2: SYSCAT.VIEWDEP catalog view
            # Always include a reference to the official documentation
            dependencies = inspector.bind.execute(f"""
                SELECT
                    referenced_schema,
                    referenced_table
                FROM mydatabase.view_dependencies
                WHERE view_schema = '{schema}'
                  AND view_name = '{view}'
            """).fetchall()

            view_urn = self.make_dataset_urn(
                self.get_db_name(inspector), schema, view
            )

            upstream_urns = []
            for dep in dependencies:
                upstream_urn = self.make_dataset_urn(
                    self.get_db_name(inspector),
                    dep.referenced_schema,
                    dep.referenced_table,
                )
                upstream_urns.append(upstream_urn)

            if upstream_urns:
                lineage_mce = make_lineage_mce(
                    source_tables=upstream_urns,
                    urn=view_urn,
                )
                yield lineage_mce.as_workunit()

        except Exception as e:
            self.report.report_warning(
                f"{schema}.{view}",
                f"Failed to extract view lineage: {e}"
            )

    @staticmethod
    def test_connection(config_dict: dict) -> TestConnectionReport:
        """
        Test connection to database and verify required permissions.

        This is called by the UI's "Test Connection" button.
        """
        test_report = TestConnectionReport()

        try:
            # Parse config
            config = MyDatabaseConfig.parse_obj(config_dict)

            # Try to connect
            url = config.get_sql_alchemy_url()
            engine = create_engine(url, **config.options)

            with engine.connect() as conn:
                # Test basic connectivity
                conn.execute("SELECT 1")
                test_report.basic_connectivity = CapabilityReport(capable=True)

                # Test schema access
                inspector = inspect(conn)
                schemas = list(inspector.get_schema_names())
                if schemas:
                    test_report.capability_report[SourceCapability.SCHEMA_METADATA] = \
                        CapabilityReport(capable=True)
                else:
                    test_report.capability_report[SourceCapability.SCHEMA_METADATA] = \
                        CapabilityReport(
                            capable=False,
                            failure_reason="Cannot access any schemas. Check permissions."
                        )

                # Test profiling capability
                if config.is_profiling_enabled():
                    try:
                        # Try to query a table
                        test_table = conn.execute(f"""
                            SELECT * FROM {schemas[0]}.* LIMIT 1
                        """)
                        test_report.capability_report[SourceCapability.DATA_PROFILING] = \
                            CapabilityReport(capable=True)
                    except Exception as e:
                        test_report.capability_report[SourceCapability.DATA_PROFILING] = \
                            CapabilityReport(
                                capable=False,
                                failure_reason=f"Cannot query tables: {str(e)}"
                            )

        except Exception as e:
            test_report.basic_connectivity = CapabilityReport(
                capable=False,
                failure_reason=f"Failed to connect: {str(e)}"
            )

        return test_report
```

### 3. Handle Custom Types

**Type Mapping Pattern**:

```python
from datahub.metadata.schema_classes import (
    ArrayTypeClass,
    BooleanTypeClass,
    BytesTypeClass,
    DateTypeClass,
    NullTypeClass,
    NumberTypeClass,
    RecordTypeClass,
    StringTypeClass,
    TimeTypeClass,
)
from datahub.ingestion.source.sql.sql_types import (
    MapTypeClass,  # For key-value maps
)

# Register before class definition
try:
    from sqlalchemy_mydatabase.types import (
        ARRAY,
        JSON,
        TIMESTAMP,
        GEOGRAPHY,
        VARIANT,
    )

    register_custom_type(ARRAY, ArrayTypeClass)
    register_custom_type(JSON, RecordTypeClass)
    register_custom_type(TIMESTAMP, TimeTypeClass)
    register_custom_type(GEOGRAPHY, BytesTypeClass)
    register_custom_type(VARIANT, RecordTypeClass)

except ImportError:
    logger.info("SQLAlchemy dialect not installed, type mapping unavailable")
```

**Type Resolution in Source**:

```python
from sqlalchemy.types import TypeDecorator

def get_column_type(
    self, dataset_name: str, column_name: str, column_type: TypeEngine
) -> SchemaFieldDataType:
    """
    Override this method for complex type handling.

    Default implementation handles standard SQL types + registered custom types.
    Override for advanced scenarios like:
    - Nested types (struct/array combinations)
    - Parameterized types
    - Database-specific type quirks
    """
    # Unwrap TypeDecorator
    if isinstance(column_type, TypeDecorator):
        column_type = column_type.impl

    # Handle complex nested types
    if isinstance(column_type, STRUCT):
        fields = []
        for field_name, field_type in column_type.fields:
            fields.append(
                SchemaField(
                    fieldPath=field_name,
                    type=self.get_column_type(dataset_name, field_name, field_type),
                    nativeDataType=str(field_type),
                )
            )
        return SchemaFieldDataType(type=RecordTypeClass(fields=fields))

    # Fallback to default implementation
    return super().get_column_type(dataset_name, column_name, column_type)
```

### 4. Advanced Authentication

**Token Refresh Pattern** (OAuth, short-lived tokens):

```python
from sqlalchemy import event

class TokenRefreshManager:
    def __init__(self, config):
        self.config = config
        self._cached_token = None
        self._token_expiry = None

    def get_token(self) -> str:
        """Get valid token, refreshing if needed"""
        if self._is_token_expired():
            self._refresh_token()
        return self._cached_token

    def _refresh_token(self):
        # Call token API
        response = requests.post(
            "https://auth.mydatabase.com/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.config.refresh_token.get_secret_value(),
            }
        )
        self._cached_token = response.json()["access_token"]
        self._token_expiry = time.time() + response.json()["expires_in"]

def _setup_token_refresh_listener(self, engine):
    """Setup SQLAlchemy event listener for token injection"""
    def do_connect_listener(_dialect, _conn_rec, _cargs, cparams):
        # Inject fresh token on every connection
        cparams["password"] = self._token_manager.get_token()

    event.listen(engine, "do_connect", do_connect_listener)
```

**AWS IAM Authentication Pattern** (RDS):

```python
from datahub.ingestion.source.sql.rds_iam_utils import RDSIAMTokenManager

def __init__(self, config, ctx):
    super().__init__(config, ctx, self.get_platform())

    if config.connection.use_aws_iam:
        self._iam_token_manager = RDSIAMTokenManager(
            endpoint=config.connection.host_port.split(":")[0],
            username=config.connection.username,
            port=int(config.connection.host_port.split(":")[1]),
            aws_config=config.connection.aws_config,
        )

def _setup_iam_listener(self, engine):
    def do_connect_listener(_dialect, _conn_rec, _cargs, cparams):
        cparams["password"] = self._iam_token_manager.get_token()
        cparams["sslmode"] = "require"

    event.listen(engine, "do_connect", do_connect_listener)
```

### 5. Two-Tier Databases (No Schema Layer)

For databases like MySQL, MongoDB that only have database.table hierarchy:

```python
from datahub.ingestion.source.sql.two_tier_sql_source import (
    TwoTierSQLAlchemySource
)

@platform_name("MySQL")
@config_class(MySQLConfig)
class MySQLSource(TwoTierSQLAlchemySource):
    """
    Two-tier source where 'schema' is actually the database name.

    Hierarchy: database.table (no schema layer)
    """

    def get_identifier(self, *, schema: str, entity: str, **kwargs) -> str:
        # In two-tier, schema parameter is actually database name
        return f"{schema}.{entity}"

    def get_allowed_schemas(self, inspector: Inspector, db_name: str):
        # Return database name as the "schema"
        yield db_name
```

## Filtering Table Types: Extract Only Permanent Tables

### Overview

SQL databases contain various entity types beyond permanent tables (temporary tables, system tables, internal views, etc.). DataHub sources should extract only meaningful, permanent entities by default while allowing users to customize what gets ingested.

**Standard Entity Types**:

- **Permanent Tables** (TABLE) - Standard database tables with persistent storage ✅ Extract by default
- **Views** (VIEW) - Logical SQL views ✅ Extract by default
- **Materialized Views** (MATERIALIZED_VIEW) - Cached query results ✅ Extract by default
- **External Tables** (EXTERNAL_TABLE) - References to external data ✅ Extract by default
- **Temporary Tables** - Session/transaction-scoped tables ❌ Exclude by default
- **System Tables** - Database internal metadata ❌ Exclude by default
- **Staging Tables** - Intermediate processing tables ⚠️ Consider excluding

### Configuration Pattern

Provide users with fine-grained control over what entity types to extract:

```python
from datahub.configuration.common import AllowDenyPattern
from datahub.ingestion.source.sql.sql_config import SQLCommonConfig

class MyDatabaseConfig(SQLCommonConfig):
    """Configuration with table type filtering"""

    # Separate patterns for different entity types
    table_pattern: AllowDenyPattern = Field(
        default=AllowDenyPattern.allow_all(),
        description="Regex patterns to filter tables. "
        "Note: Temporary tables are automatically excluded."
    )

    view_pattern: AllowDenyPattern = Field(
        default=AllowDenyPattern.allow_all(),
        description="Regex patterns to filter views. "
        "If not specified, table_pattern is applied to views as well."
    )

    # Feature toggles for entity types
    include_views: bool = Field(
        default=True,
        description="Whether to ingest views"
    )

    include_materialized_views: bool = Field(
        default=True,
        description="Whether to ingest materialized views"
    )

    # Apply table_pattern to view_pattern if not specified
    @model_validator(mode="before")
    @classmethod
    def view_pattern_is_table_pattern_unless_specified(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        view_pattern = values.get("view_pattern")
        table_pattern = values.get("table_pattern")
        if table_pattern and not view_pattern:
            logger.info(f"Applying table_pattern {table_pattern} to view_pattern.")
            values["view_pattern"] = table_pattern
        return values
```

**Why Separate Patterns?**

- Users may want different filtering for tables vs views
- Allows exclude patterns specific to each entity type
- Maintains backward compatibility with existing configurations

### Identifying Table Types

#### Using SQLAlchemy Inspector (Recommended)

SQLAlchemy Inspector provides native separation of tables and views:

```python
from sqlalchemy.engine.reflection import Inspector

def get_workunits_internal(
    self, inspector: Inspector, schema: str
) -> Iterable[MetadataWorkUnit]:
    """Extract metadata with table type filtering"""

    # SQLAlchemy separates tables and views by default
    if self.config.include_tables:
        for table_name in inspector.get_table_names(schema=schema):
            # Verify it's a permanent table
            if self._is_permanent_table(inspector, schema, table_name):
                yield from self._process_table(inspector, schema, table_name)

    if self.config.include_views:
        for view_name in inspector.get_view_names(schema=schema):
            yield from self._process_view(inspector, schema, view_name)
```

#### Querying INFORMATION_SCHEMA

For detailed table type information, query the standard INFORMATION_SCHEMA:

```python
def _is_permanent_table(
    self, inspector: Inspector, schema: str, table: str
) -> bool:
    """
    Check if a table is a permanent table (not temporary or system table).

    References:
    - PostgreSQL: https://www.postgresql.org/docs/current/infoschema-tables.html
    - MySQL: https://dev.mysql.com/doc/refman/8.0/en/information-schema-tables-table.html
    """
    try:
        result = inspector.bind.execute(f"""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
              AND table_name = '{table}'
        """).fetchone()

        if not result:
            return False

        table_type = result.table_type.upper()

        # Include permanent tables
        if table_type in ('BASE TABLE', 'TABLE'):
            return True

        # Exclude temporary and system tables
        if table_type in ('LOCAL TEMPORARY', 'GLOBAL TEMPORARY', 'SYSTEM TABLE'):
            return False

        # Check if table is in a temporary schema
        if self._is_temporary_schema(schema):
            return False

        return True

    except Exception as e:
        self.report.warning(
            title="Failed to determine table type",
            message=f"Assuming permanent table: {schema}.{table}",
            context=f"{schema}.{table}",
            exc=e,
        )
        return True  # Default to including on error
```

#### Database-Specific Temporary Table Detection

**PostgreSQL**:

```python
def _is_temporary_schema(self, schema: str) -> bool:
    """PostgreSQL temporary tables are in pg_temp_* schemas"""
    return schema.startswith('pg_temp')

# Alternative: Check pg_class system catalog
def _is_temporary_table_postgres(
    self, inspector: Inspector, schema: str, table: str
) -> bool:
    """
    Reference: https://www.postgresql.org/docs/current/catalog-pg-class.html
    relpersistence: 'p' = permanent, 't' = temporary, 'u' = unlogged
    """
    result = inspector.bind.execute(f"""
        SELECT relpersistence
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = '{schema}'
          AND c.relname = '{table}'
    """).fetchone()

    return result and result.relpersistence == 't'
```

**MySQL**:

```python
def _is_temporary_table_mysql(
    self, inspector: Inspector, schema: str, table: str
) -> bool:
    """
    MySQL temporary tables are session-scoped and not visible in INFORMATION_SCHEMA.
    If a table appears in INFORMATION_SCHEMA.TABLES, it's permanent.

    Reference: https://dev.mysql.com/doc/refman/8.0/en/information-schema-tables-table.html
    """
    # MySQL doesn't show temporary tables in INFORMATION_SCHEMA
    # If we can query it here, it's permanent
    return False
```

**Snowflake**:

```python
def _is_temporary_table_snowflake(
    self, inspector: Inspector, schema: str, table: str
) -> bool:
    """
    Snowflake temporary tables have table_type = 'TEMPORARY'

    Reference: https://docs.snowflake.com/en/sql-reference/info-schema/tables
    """
    result = inspector.bind.execute(f"""
        SELECT table_type
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
          AND table_name = '{table}'
    """).fetchone()

    return result and result.table_type == 'TEMPORARY'
```

**BigQuery**:

```python
def _is_temporary_table_bigquery(
    self, inspector: Inspector, dataset: str, table: str
) -> bool:
    """
    BigQuery temporary tables are prefixed with '_SESSION' or created in temp datasets.

    Reference: https://cloud.google.com/bigquery/docs/tables#table-naming
    """
    # Temporary tables start with _SESSION or are in session-scoped datasets
    if table.startswith('_SESSION'):
        return True

    # Check if in temporary dataset (datasets starting with _)
    if dataset.startswith('_'):
        return True

    return False
```

### Extracting Table Metadata with Type Information

Add table type information to dataset properties for user visibility:

```python
from datahub.metadata.schema_classes import DatasetPropertiesClass

def get_extra_table_properties(
    self, inspector: Inspector, schema: str, table: str
) -> Optional[Dict[str, Any]]:
    """
    Extract table type and other metadata.

    This information is stored in DatasetProperties.customProperties
    """
    try:
        result = inspector.bind.execute(f"""
            SELECT
                table_type,
                table_catalog,
                create_time,
                update_time
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
              AND table_name = '{table}'
        """).fetchone()

        if result:
            properties = {
                "table_type": result.table_type,
                "catalog": result.table_catalog,
            }

            if result.create_time:
                properties["create_time"] = str(result.create_time)
            if result.update_time:
                properties["update_time"] = str(result.update_time)

            return properties

    except Exception as e:
        self.report.warning(
            title="Failed to get table metadata",
            message="Skipping extra properties",
            context=f"{schema}.{table}",
            exc=e,
        )

    return None
```

### Setting Dataset Subtypes

Map database table types to DataHub standard subtypes:

```python
from datahub.metadata.schema_classes import SubTypesClass

def get_dataset_subtype(
    self, inspector: Inspector, schema: str, entity: str, entity_type: str
) -> Optional[SubTypesClass]:
    """
    Map database entity types to DataHub subtypes.

    Standard DataHub subtypes:
    - TABLE: Standard database tables (permanent storage)
    - VIEW: SQL views (logical representations)
    - MATERIALIZED_VIEW: Materialized views (stored results)
    - EXTERNAL_TABLE: External data sources (S3, GCS, etc.)
    - DYNAMIC_TABLE: Auto-refreshing tables (Snowflake)
    """

    # Query actual table type from database
    result = inspector.bind.execute(f"""
        SELECT table_type
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
          AND table_name = '{entity}'
    """).fetchone()

    if not result:
        return None

    table_type = result.table_type.upper()

    # Map to DataHub subtypes
    if table_type in ('BASE TABLE', 'TABLE'):
        # Check if external table
        if self._is_external_table(inspector, schema, entity):
            return SubTypesClass(typeNames=["EXTERNAL_TABLE"])
        return SubTypesClass(typeNames=["TABLE"])

    elif table_type == 'VIEW':
        # Check if materialized
        if self._is_materialized_view(inspector, schema, entity):
            return SubTypesClass(typeNames=["MATERIALIZED_VIEW"])
        return SubTypesClass(typeNames=["VIEW"])

    elif table_type == 'MATERIALIZED VIEW':
        return SubTypesClass(typeNames=["MATERIALIZED_VIEW"])

    return None

def _is_external_table(
    self, inspector: Inspector, schema: str, table: str
) -> bool:
    """Check if table is external (data stored outside database)"""
    # Implementation varies by database
    # Example for Snowflake:
    try:
        result = inspector.bind.execute(f"""
            SHOW EXTERNAL TABLES LIKE '{table}' IN SCHEMA {schema}
        """).fetchone()
        return result is not None
    except:
        return False
```

### Reporting Filtered Entities

Track what was filtered and why:

```python
from dataclasses import dataclass, field
from datahub.ingestion.source.state.stale_entity_removal_handler import (
    StaleEntityRemovalSourceReport
)
from datahub.ingestion.source.sql.sql_common import SQLSourceReport

@dataclass
class MyDatabaseReport(SQLSourceReport):
    """Custom report tracking filtered entities"""

    # Entity counts by type
    permanent_tables_scanned: int = 0
    views_scanned: int = 0
    materialized_views_scanned: int = 0
    external_tables_scanned: int = 0

    # Filtered entities (with reasons)
    temporary_tables_filtered: LossyList[str] = field(default_factory=LossyList)
    system_tables_filtered: LossyList[str] = field(default_factory=LossyList)

    def report_entity_scanned(self, entity_type: str) -> None:
        """Increment counter for entity type"""
        if entity_type == "table":
            self.permanent_tables_scanned += 1
        elif entity_type == "view":
            self.views_scanned += 1
        elif entity_type == "materialized_view":
            self.materialized_views_scanned += 1
        elif entity_type == "external_table":
            self.external_tables_scanned += 1

    def report_temporary_table_filtered(self, table_name: str) -> None:
        """Track filtered temporary table"""
        self.temporary_tables_filtered.append(table_name)

    def report_system_table_filtered(self, table_name: str) -> None:
        """Track filtered system table"""
        self.system_tables_filtered.append(table_name)
```

**Usage in Source**:

```python
# In table processing loop
if self._is_temporary_table(inspector, schema, table):
    self.report.report_temporary_table_filtered(f"{schema}.{table}")
    continue  # Skip temporary table

# For successfully processed table
self.report.report_entity_scanned("table")
```

### Complete Example: PostgreSQL with Table Type Filtering

```python
from typing import Iterable, Optional, Dict, Any
from sqlalchemy.engine.reflection import Inspector

from datahub.ingestion.source.sql.sql_common import SQLAlchemySource
from datahub.metadata.schema_classes import SubTypesClass

class PostgresSource(SQLAlchemySource):
    """PostgreSQL source with comprehensive table type filtering"""

    def get_workunits_internal(
        self, inspector: Inspector, schema: str
    ) -> Iterable[MetadataWorkUnit]:
        """Extract only permanent tables and user-defined views"""

        # Skip system schemas
        if self._is_system_schema(schema):
            self.report.report_system_table_filtered(f"schema:{schema}")
            return

        # Skip temporary schemas (pg_temp_*)
        if schema.startswith('pg_temp'):
            self.report.report_temporary_table_filtered(f"schema:{schema}")
            return

        # Process permanent tables
        for table in inspector.get_table_names(schema=schema):
            # Apply table pattern
            if not self.config.table_pattern.allowed(table):
                self.report.report_dropped(f"{schema}.{table}")
                continue

            # Check if temporary (via pg_catalog)
            if self._is_temporary_table(inspector, schema, table):
                self.report.report_temporary_table_filtered(f"{schema}.{table}")
                continue

            # Process permanent table
            self.report.report_entity_scanned("table")
            yield from self._process_table(inspector, schema, table)

        # Process views if enabled
        if self.config.include_views:
            for view in inspector.get_view_names(schema=schema):
                if not self.config.view_pattern.allowed(view):
                    self.report.report_dropped(f"{schema}.{view}")
                    continue

                # Check if materialized view
                if self._is_materialized_view(inspector, schema, view):
                    if self.config.include_materialized_views:
                        self.report.report_entity_scanned("materialized_view")
                        yield from self._process_view(
                            inspector, schema, view, is_materialized=True
                        )
                else:
                    self.report.report_entity_scanned("view")
                    yield from self._process_view(inspector, schema, view)

    def _is_system_schema(self, schema: str) -> bool:
        """
        Check if schema is a PostgreSQL system schema.
        Reference: https://www.postgresql.org/docs/current/ddl-schemas.html
        """
        return schema in ('information_schema', 'pg_catalog', 'pg_toast')

    def _is_temporary_table(
        self, inspector: Inspector, schema: str, table: str
    ) -> bool:
        """
        Check via pg_class.relpersistence.
        Reference: https://www.postgresql.org/docs/current/catalog-pg-class.html
        """
        try:
            result = inspector.bind.execute(f"""
                SELECT relpersistence
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = '{schema}'
                  AND c.relname = '{table}'
            """).fetchone()

            return result and result.relpersistence == 't'
        except Exception:
            return False

    def _is_materialized_view(
        self, inspector: Inspector, schema: str, view: str
    ) -> bool:
        """
        Check pg_class.relkind for materialized views.
        Reference: https://www.postgresql.org/docs/current/catalog-pg-class.html
        relkind: 'r' = table, 'v' = view, 'm' = materialized view
        """
        try:
            result = inspector.bind.execute(f"""
                SELECT relkind
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = '{schema}'
                  AND c.relname = '{view}'
            """).fetchone()

            return result and result.relkind == 'm'
        except Exception:
            return False

    def get_dataset_subtype(
        self, inspector: Inspector, schema: str, entity: str
    ) -> Optional[SubTypesClass]:
        """Assign correct DataHub subtype"""
        try:
            result = inspector.bind.execute(f"""
                SELECT relkind
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = '{schema}'
                  AND c.relname = '{entity}'
            """).fetchone()

            if not result:
                return None

            relkind = result.relkind

            # Map PostgreSQL relkind to DataHub subtypes
            if relkind == 'r':  # Regular table
                return SubTypesClass(typeNames=["TABLE"])
            elif relkind == 'v':  # View
                return SubTypesClass(typeNames=["VIEW"])
            elif relkind == 'm':  # Materialized view
                return SubTypesClass(typeNames=["MATERIALIZED_VIEW"])
            elif relkind == 'f':  # Foreign table (external)
                return SubTypesClass(typeNames=["EXTERNAL_TABLE"])

        except Exception:
            pass

        return None
```

### Best Practices Summary

1. **Default Behavior**: Extract permanent tables, views, and materialized views by default
2. **Exclude Automatically**: Temporary tables, system tables, session-scoped tables
3. **Configuration Control**: Provide `table_pattern`, `view_pattern`, and feature toggles
4. **Use SQLAlchemy Inspector**: Leverage `get_table_names()` and `get_view_names()` for primary separation
5. **Query System Catalogs**: Use INFORMATION_SCHEMA or database-specific catalogs for detailed type info
6. **Report Filtering**: Track what was filtered and why using report metrics
7. **Set Subtypes**: Map database types to standard DataHub subtypes (TABLE, VIEW, etc.)
8. **Document References**: Include official database documentation links in code comments
9. **Handle Errors Gracefully**: Default to including entities if type detection fails
10. **Smart Pattern Application**: Apply `table_pattern` to `view_pattern` when not specified

## Common SQL Source Patterns

### Stored Procedures

```python
from datahub.ingestion.source.sql.stored_procedures.base import BaseProcedure

def get_procedures_for_schema(
    self, inspector: Inspector, schema: str, db_name: str
) -> Iterable[BaseProcedure]:
    """Extract stored procedures/functions"""
    procedures = inspector.bind.execute(f"""
        SELECT
            routine_name as name,
            routine_definition as definition,
            external_language as language,
            routine_comment as description
        FROM information_schema.routines
        WHERE routine_schema = '{schema}'
          AND routine_type IN ('PROCEDURE', 'FUNCTION')
    """)

    for proc in procedures:
        yield BaseProcedure(
            name=proc.name,
            definition=proc.definition,
            language=proc.language,
            description=proc.description,
        )
```

### Partition Support

```python
def get_table_properties(
    self, inspector: Inspector, schema: str, table: str
) -> Optional[DatasetProperties]:
    """Add partition information to table properties"""
    properties = super().get_table_properties(inspector, schema, table)

    # Query partition metadata
    partitions = inspector.bind.execute(f"""
        SELECT
            partition_expression,
            partition_strategy
        FROM information_schema.partitions
        WHERE table_schema = '{schema}'
          AND table_name = '{table}'
    """).fetchone()

    if partitions and properties:
        properties.customProperties["partition_expression"] = partitions.partition_expression
        properties.customProperties["partition_strategy"] = partitions.partition_strategy

    return properties
```

## Required Aspects for SQL Database Sources

**Every SQL source MUST emit these aspects. Missing aspects indicate INCOMPLETE implementation.**

### Understanding Aspect Requirements

- **✅ ALWAYS**: Must be emitted for every entity of this type
- **✅ IF SOURCE PROVIDES**: Must be emitted if the source system provides this information
- **✅ IF FEATURE ENABLED**: Must be emitted when the corresponding feature is enabled in config
- **🔄 AUTO-GENERATED**: Automatically generated by the pipeline from other aspects

### Auto-Generated Aspects (by DataHub Pipeline)

These aspects are automatically generated and do NOT need to be explicitly emitted:

| Aspect          | Generated From     | Notes                                   |
| --------------- | ------------------ | --------------------------------------- |
| `browsePathsV2` | `container` aspect | Auto-generated from container hierarchy |
| `status`        | All entities       | Auto-generated for all entities         |

### Required Aspects for Datasets (Tables/Views)

| Aspect                   | Required                | Description                                                                                                                                                 |
| ------------------------ | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dataPlatformInstance`   | ✅ ALWAYS               | Links entity to data platform (e.g., `urn:li:dataPlatform:postgres`). **Always required** - holds platform reference even without platform_instance config. |
| `containerProperties`    | ✅ ALWAYS               | For databases/schemas as containers                                                                                                                         |
| `subTypes`               | ✅ ALWAYS               | Identifies entity subtype (Table, View, Database, Schema)                                                                                                   |
| `container`              | ✅ ALWAYS               | Links datasets to parent containers                                                                                                                         |
| `datasetProperties`      | ✅ ALWAYS               | Dataset name, qualified name, custom properties                                                                                                             |
| `schemaMetadata`         | ✅ ALWAYS               | Column definitions with types                                                                                                                               |
| `viewProperties`         | ✅ IF VIEW              | View definition SQL (required for all views)                                                                                                                |
| `upstreamLineage`        | ✅ IF LINEAGE ENABLED   | Upstream table dependencies (required when `include_view_lineage=true`)                                                                                     |
| `globalTags`             | ✅ IF SOURCE PROVIDES   | Tags from source system (required if source has tags/labels)                                                                                                |
| `ownership`              | ✅ IF SOURCE PROVIDES   | Ownership info from source (required if source exposes owners)                                                                                              |
| `datasetProfile`         | ✅ IF PROFILING ENABLED | Row counts, column stats (required when profiling is enabled)                                                                                               |
| `datasetUsageStatistics` | ✅ IF USAGE ENABLED     | Query log usage (required when usage extraction is implemented)                                                                                             |

### Common Mistakes

1. **Missing `dataPlatformInstance`**: This aspect is ALWAYS required, not just when `platform_instance` is configured. It links every entity to its data platform URN.

2. **Missing `globalTags` when source has tags**: If the source system has a tags/labels API (e.g., BigQuery labels, Snowflake tags), you MUST extract and emit them.

3. **Missing `ownership` when source has owners**: If the source system exposes ownership information (e.g., table owners, schema owners), you MUST extract and emit it.

4. **Missing `upstreamLineage` for views**: If `include_view_lineage` is enabled and the view has a parseable definition, lineage MUST be emitted.

### Example: Emitting dataPlatformInstance

```python
from datahub.emitter.mce_builder import (
    make_data_platform_urn,
    make_dataplatform_instance_urn,
)
from datahub.metadata.schema_classes import DataPlatformInstanceClass

def _emit_data_platform_instance(self, dataset_urn: str) -> MetadataWorkUnit:
    """Always emit dataPlatformInstance - required for all datasets."""
    instance_urn = None
    if self.config.platform_instance:
        instance_urn = make_dataplatform_instance_urn(
            self.platform, self.config.platform_instance
        )

    return MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=DataPlatformInstanceClass(
            platform=make_data_platform_urn(self.platform),
            instance=instance_urn,
        ),
    ).as_workunit()
```

## Next Steps

- See [Common Patterns Guide](patterns.md) for URN generation, error handling, and more
- See [Lineage Extraction Guide](lineage.md) for implementing lineage
- See [Testing Guide](testing.md) for testing strategies
- See [Registration & Documentation Guide](registration.md) for final steps

---

## Related Guides

- [Main Guide](main.md) - Overview and quick start
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [API-Based Sources](api.md) - For REST/GraphQL API sources
- [Common Patterns](patterns.md) - Shared patterns and utilities
- [Lineage Extraction](lineage.md) - Implementing lineage
- [Container Creation](containers.md) - Creating containers (databases, schemas)
- [Testing](testing.md) - Testing strategies
