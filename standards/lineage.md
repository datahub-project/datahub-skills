# Lineage Extraction Guide

This guide covers how to implement lineage extraction for your source.

## Related Guides

- [Main Guide](main.md) - Overview and quick start
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [SQL Sources](sql.md) - For SQL database sources
- [API-Based Sources](api.md) - For REST/GraphQL API sources
- [Common Patterns](patterns.md) - Shared patterns and utilities
- [Performance](performance.md) - Performance and memory optimization
- [Testing](testing.md) - Testing strategies
- [Registration & Documentation](registration.md) - Final steps

## Lineage Extraction

Lineage extraction is a critical feature that shows how data flows through your systems. DataHub supports multiple methods for extracting lineage, depending on your source type.

### Overview of Lineage Extraction Methods

1. **SQL Parsing** - Parse SQL queries (views, stored procedures, queries) to extract table and column-level lineage
2. **API-Based Lineage** - Extract lineage from platform APIs (BI tools, transformation tools)
3. **System Tables** - Query database system tables for view dependencies
4. **Audit Logs** - Parse query logs to infer lineage from actual query execution

### 🔴 CRITICAL: Query Log Lineage vs View Lineage

**IMPORTANT**: When implementing lineage for SQL databases, you should plan for TWO types of lineage:

#### 1. **View-Based Lineage** (Structural)

- **Source**: View definitions from `information_schema.views`
- **Captures**: View → Table lineage from CREATE VIEW statements
- **Always available**: No special configuration required
- **Column-level**: Yes (via SQL parsing)
- **Limitations**: Only captures lineage from views, not operational data flows

#### 2. **Query Log Lineage** (Operational) ⭐ **DON'T FORGET THIS**

- **Source**: Executed queries from audit logs / query history tables
- **Captures**: Table → Table lineage from actual queries:
  - `INSERT INTO target SELECT ... FROM source`
  - `CREATE TABLE target AS SELECT ... FROM source`
  - ETL and data pipeline operations
- **Requires**: Audit log or query history enabled
- **Column-level**: Table-level in most implementations (column-level optional)
- **Advantages**: Captures real-world data flows that views don't show

**✅ Best Practice**: Implement BOTH types of lineage for complete coverage:

- View lineage: Captures structural dependencies
- Query log lineage: Captures operational data flows
- Together: Complete lineage picture

**⚠️ Common Mistake**: Implementing only view lineage and forgetting query log lineage.

#### Planning Checklist

When creating your planning document, explicitly address:

- [ ] **View lineage**: Will you extract from view definitions? (Usually: YES)
- [ ] **Query log lineage**: Does the database have audit logs / query history?
  - If YES: Plan to implement query log lineage extraction
  - If NO: Document why it's not available
- [ ] **Time windows**: Use `BaseTimeWindowConfig` for query log time ranges (NOT custom lookback fields)
- [ ] **Configuration**: Separate config classes for usage vs lineage (both extend `BaseTimeWindowConfig`)

### Checking for Audit Log Capabilities

Before implementing lineage extraction, you should check if the database/platform provides audit logs or query history that can be used for lineage extraction. This is important because:

- **Audit logs provide real-world lineage** - They show actual data flows based on executed queries, not just definitions
- **Better coverage** - Can capture lineage from ad-hoc queries, ETL jobs, and other sources not visible in view definitions
- **Usage patterns** - Can also provide usage statistics alongside lineage

#### How to Check for Audit Log Support

1. **Consult Official Documentation**:
   - Search for "audit log", "query history", "query log", or "access log" in the database/platform documentation
   - Look for system tables, views, or APIs that store query execution history
   - Check if there are specific permissions required to access audit logs

2. **Common Audit Log Locations**:
   - **Snowflake**: `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` (see [Snowflake Query History](https://docs.snowflake.com/en/sql-reference/account-usage/query_history.html))
   - **BigQuery**: Cloud Logging API or `INFORMATION_SCHEMA.JOBS*` views (see [BigQuery Audit Logs](https://cloud.google.com/bigquery/docs/audit-logs))
   - **Redshift**: `SYS_QUERY_HISTORY` and `SYS_QUERY_DETAIL` system tables (see [Redshift System Tables](https://docs.aws.amazon.com/redshift/latest/dg/c_intro_system_tables.html))
   - **PostgreSQL**: `pg_stat_statements` extension (see [PostgreSQL Statistics](https://www.postgresql.org/docs/current/pgstatstatements.html))
   - **MySQL**: General Query Log or Performance Schema (see [MySQL Logging](https://dev.mysql.com/doc/refman/8.0/en/logging.html))

3. **Document Your Findings**:
   - If audit logs are available, document:
     - The system table/view/API name
     - Required permissions
     - Link to official documentation
     - Any limitations (retention period, query format, etc.)
   - If audit logs are NOT available, document:
     - What was checked (specific documentation pages)
     - Why they're not available (feature not supported, requires enterprise license, etc.)
     - Alternative lineage sources (view definitions, stored procedures, etc.)

4. **Update Capability Annotations**:

   ```python
   # If audit logs are available:
   @capability(SourceCapability.LINEAGE_COARSE, "Enabled via audit logs and view SQL parsing")
   @capability(SourceCapability.LINEAGE_FINE, "Enabled via audit logs and view SQL parsing")

   # If audit logs are NOT available:
   @capability(SourceCapability.LINEAGE_COARSE, "Enabled by default for views via SQL parsing. Note: No audit log lineage support.")
   @capability(SourceCapability.LINEAGE_FINE, "Enabled by default for views via SQL parsing. Note: No audit log lineage support.")
   ```

5. **Add Comments in Source Code**:

   ```python
   # Audit Log Investigation:
   # Checked IBM DB2 documentation for audit log capabilities:
   # - Reference: https://www.ibm.com/docs/en/db2-for-zos/12?topic=auditing
   # - DB2 Audit Facility exists but requires specific configuration
   # - Query history available via SYSIBMADM views (if enabled)
   # - Conclusion: Audit log lineage not implemented due to:
   #   1. Requires DB2 Audit Facility to be enabled (not default)
   #   2. Requires specific permissions (AUDIT privilege)
   #   3. Query format may not be suitable for automatic parsing
   # - Alternative: Using view SQL parsing for lineage extraction
   ```

### SQL Parsing for Lineage

SQL parsing is the most powerful method for extracting lineage from SQL-based sources. It can extract both **table-level** (coarse) and **column-level** (fine-grained) lineage.

#### 🟡 MAJOR ISSUE: Use SqlParsingAggregator for Lineage Generation

**When implementing SQL-based lineage, prefer using `SqlParsingAggregator` over direct `sqlglot_lineage()` calls.**

`SqlParsingAggregator` is a comprehensive SQL parsing orchestrator that provides:

- **Deferred view parsing**: View definitions are parsed after all schemas are registered
- **Schema resolution**: Integrates with `SchemaResolver` to resolve table/column references
- **Temp table handling**: Tracks temp tables across sessions and merges their lineage
- **Query deduplication**: Uses fingerprinting to deduplicate identical queries
- **Detailed reporting**: Built-in `SqlAggregatorReport` with metrics
- **Query entities**: Optionally generates `Query` entities with metadata

**✅ PREFERRED: Use SqlParsingAggregator**

```python
from datahub.sql_parsing.sql_parsing_aggregator import SqlParsingAggregator

class MySource(StatefulIngestionSourceBase):
    def __init__(self, config, ctx):
        super().__init__(config, ctx)

        # Initialize aggregator for lineage extraction
        self.aggregator = SqlParsingAggregator(
            platform=self.platform,
            platform_instance=config.platform_instance,
            env=config.env,
            graph=ctx.graph,
            generate_lineage=config.include_view_lineage,
            generate_queries=False,  # Set True if you want Query entities
            generate_usage_statistics=False,
            generate_operations=False,
        )

    def _process_table(self, table) -> Iterable[MetadataWorkUnit]:
        # ... emit table metadata ...

        # Register schema with aggregator for lineage resolution
        if schema_metadata:
            self.aggregator.register_schema(dataset_urn, schema_metadata)

    def _process_view(self, view) -> Iterable[MetadataWorkUnit]:
        # ... emit view metadata ...

        # Register view definition for deferred lineage parsing
        if view_definition:
            self.aggregator.add_view_definition(
                view_urn=dataset_urn,
                view_definition=view_definition,
                default_db=catalog,
                default_schema=schema,
            )

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        # Process tables first (to populate schema resolver)
        yield from self._process_tables()

        # Process views
        yield from self._process_views()

        # Generate lineage AFTER all schemas are registered
        for mcp in self.aggregator.gen_metadata():
            yield mcp.as_workunit()

    def close(self):
        self.aggregator.close()
        super().close()
```

**⚠️ ACCEPTABLE BUT NOT PREFERRED: Direct sqlglot_lineage() calls**

Use direct `sqlglot_lineage()` only when:

- You're processing a single SQL statement in isolation
- You don't need schema resolution for column-level lineage
- You're in a non-SQL source (e.g., BI tool with embedded SQL)

```python
# Only use this for simple cases or non-SQL sources
from datahub.sql_parsing.sqlglot_lineage import sqlglot_lineage

result = sqlglot_lineage(
    sql=sql_query,
    schema_resolver=schema_resolver,
    default_db=database,
    default_schema=schema,
)
```

---

#### When to Use SQL Parsing

SQL parsing can be used by sources that:

- Have SQL queries available (view definitions, stored procedures, query logs)
- Support standard SQL dialects (PostgreSQL, MySQL, SQL Server, etc.)
- Need to extract column-level lineage

**Source Types That Can Use SQL Parsing:**

- ✅ **SQL Databases** - PostgreSQL, MySQL, SQL Server, Oracle, etc. (via `SQLAlchemySource`)
- ✅ **Data Warehouses** - Snowflake, Redshift, BigQuery (view definitions and query logs)
- ✅ **Query Engines** - Dremio, Trino, Hive (view definitions)
- ✅ **BI Tools** - Tableau (Custom SQL), Looker (LookML SQL), Power BI (M Query → SQL), Superset, Metabase, Mode
- ✅ **Transformation Tools** - dbt (model SQL), Airflow (SQL operators)
- ✅ **Streaming Platforms** - Kafka Connect (SQL-based connectors)

#### Implementation Pattern for SQL Sources

For sources extending `SQLAlchemySource`, SQL parsing is built-in:

```python
from datahub.sql_parsing.sql_parsing_aggregator import SqlParsingAggregator

class MyDatabaseSource(SQLAlchemySource):
    def __init__(self, config, ctx):
        super().__init__(config, ctx, self.get_platform())

        # SqlParsingAggregator is automatically initialized in SQLAlchemySource
        # It handles view lineage extraction when include_view_lineage is enabled

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        # Process tables and views
        yield from super().get_workunits_internal()

        # Generate lineage workunits from SQL parsing
        yield from self._generate_aggregator_workunits()
```

**Configuration:**

```python
class MyDatabaseConfig(SQLCommonConfig):
    # Enable view lineage extraction
    include_view_lineage: bool = Field(
        default=True,
        description="Extract lineage from view definitions"
    )

    # Enable column-level lineage (requires include_view_lineage=True)
    include_view_column_lineage: bool = Field(
        default=True,
        description="Extract column-level lineage from views"
    )
```

#### Manual SQL Parsing (Non-SQL Sources)

For API-based sources that have SQL queries available (BI tools, dbt, etc.):

```python
from datahub.sql_parsing.sqlglot_lineage import (
    sqlglot_lineage,
    create_lineage_sql_parsed_result,
    SqlParsingResult,
)
from datahub.sql_parsing.schema_resolver import SchemaResolver
from datahub.metadata.schema_classes import (
    UpstreamLineageClass,
    UpstreamClass,
    FineGrainedLineageClass,
    DatasetLineageTypeClass,
)

class MyBISource(StatefulIngestionSourceBase):
    def _extract_lineage_from_sql(
        self,
        dashboard_urn: str,
        sql_query: str,
        platform: str = "postgres"
    ) -> Iterable[MetadataWorkUnit]:
        """Extract lineage from SQL query"""

        # Create schema resolver to help resolve table names
        schema_resolver = SchemaResolver(
            platform=platform,
            platform_instance=self.config.platform_instance,
            env=self.config.env,
            graph=self.ctx.graph,
        )

        # Parse SQL to extract lineage
        try:
            parsing_result: SqlParsingResult = sqlglot_lineage(
                sql=sql_query,
                schema_resolver=schema_resolver,
                default_db=None,  # Optional: default database name
                default_schema=None,  # Optional: default schema name
            )

            # Build upstream lineage
            upstreams = []
            for upstream_table in parsing_result.in_tables:
                # Convert parsed table reference to DataHub URN
                upstream_urn = self._resolve_table_to_urn(upstream_table)
                if upstream_urn:
                    upstreams.append(
                        UpstreamClass(
                            dataset=upstream_urn,
                            type=DatasetLineageTypeClass.TRANSFORMED,
                        )
                    )

            if upstreams:
                lineage = UpstreamLineageClass(upstreams=upstreams)
                yield MetadataChangeProposalWrapper(
                    entityUrn=dashboard_urn,
                    aspect=lineage,
                ).as_workunit()

            # Optional: Extract column-level lineage
            if parsing_result.column_lineage:
                fine_grained_lineage = self._build_fine_grained_lineage(
                    parsing_result.column_lineage,
                    dashboard_urn
                )
                if fine_grained_lineage:
                    yield MetadataChangeProposalWrapper(
                        entityUrn=dashboard_urn,
                        aspect=fine_grained_lineage,
                    ).as_workunit()

        except Exception as e:
            self.report.report_warning(
                f"dashboard:{dashboard_urn}",
                f"Failed to parse SQL for lineage: {e}"
            )

    def _resolve_table_to_urn(self, table_ref) -> Optional[str]:
        """Convert parsed table reference to DataHub dataset URN"""
        from datahub.emitter.mce_builder import make_dataset_urn_with_platform_instance

        # table_ref is a ColumnRef or similar object from sqlglot_lineage
        # Extract database, schema, table from the reference
        database = getattr(table_ref, 'database', None)
        schema = getattr(table_ref, 'schema', None) or getattr(table_ref, 'table', None)
        table = getattr(table_ref, 'table', None) if hasattr(table_ref, 'table') else None

        if not all([database, schema, table]):
            return None

        return make_dataset_urn_with_platform_instance(
            platform="postgres",  # Adjust based on your source
            name=f"{database}.{schema}.{table}",
            platform_instance=self.config.platform_instance,
            env=self.config.env,
        )

    def _build_fine_grained_lineage(
        self,
        column_lineage: Dict[str, List],
        downstream_urn: str
    ) -> Optional[FineGrainedLineageClass]:
        """Build fine-grained (column-level) lineage"""
        from datahub.emitter.mce_builder import make_schema_field_urn

        fine_grained = []

        for downstream_col, upstream_cols in column_lineage.items():
            for upstream_col_ref in upstream_cols:
                upstream_urn = self._resolve_table_to_urn(upstream_col_ref)
                if upstream_urn:
                    fine_grained.append(
                        FineGrainedLineageClass(
                            upstreamType=FineGrainedLineageUpstreamTypeClass.FIELD_SET,
                            upstreams=[
                                make_schema_field_urn(
                                    upstream_urn,
                                    upstream_col_ref.column
                                )
                            ],
                            downstreamType=FineGrainedLineageDownstreamTypeClass.FIELD,
                            downstreams=[
                                make_schema_field_urn(
                                    downstream_urn,
                                    downstream_col
                                )
                            ],
                        )
                    )

        return FineGrainedLineageClass(fineGrainedLineages=fine_grained) if fine_grained else None
```

#### Example: BI Tool with SQL Parsing

```python
# Example: Extracting lineage from Tableau Custom SQL
def _process_custom_sql_datasource(
    self,
    datasource: dict,
    dashboard_urn: str
) -> Iterable[MetadataWorkUnit]:
    """Process Tableau Custom SQL datasource and extract lineage"""

    custom_sql = datasource.get("query")
    if not custom_sql:
        return

    # Parse SQL to get upstream tables
    from datahub.sql_parsing.sqlglot_lineage import sqlglot_lineage
    from datahub.sql_parsing.schema_resolver import SchemaResolver

    schema_resolver = SchemaResolver(
        platform="postgres",  # Adjust based on your database
        platform_instance=self.config.platform_instance,
        env=self.config.env,
        graph=self.ctx.graph,
    )

    try:
        result = sqlglot_lineage(
            sql=custom_sql,
            schema_resolver=schema_resolver,
        )

        # Build lineage
        upstreams = []
        for table_ref in result.in_tables:
            upstream_urn = self._resolve_tableau_table_reference(table_ref)
            if upstream_urn:
                upstreams.append(
                    UpstreamClass(
                        dataset=upstream_urn,
                        type=DatasetLineageTypeClass.TRANSFORMED,
                    )
                )

        if upstreams:
            lineage = UpstreamLineageClass(upstreams=upstreams)
            yield MetadataChangeProposalWrapper(
                entityUrn=dashboard_urn,
                aspect=lineage,
            ).as_workunit()

    except Exception as e:
        self.report.report_warning(
            f"datasource:{datasource.get('id')}",
            f"Failed to extract lineage from SQL: {e}"
        )
```

### Populating SchemaResolver for Accurate Column Lineage

For SQL parsing to resolve **column-level lineage** correctly, you must populate the `SchemaResolver` with schema information as you emit datasets. Without this, `sqlglot_lineage()` can only identify tables, not columns.

> **Reference Implementation**: See `bigquery_v2/bigquery_schema_gen.py` line ~1170 where `add_schema_metadata()` is called after emitting each table's schema.

```python
from datahub.sql_parsing.schema_resolver import SchemaResolver

class MySource(StatefulIngestionSourceBase):
    def __init__(self, config, ctx):
        super().__init__(config, ctx)

        # Create resolver at source initialization
        self.schema_resolver = SchemaResolver(
            platform=self.platform,
            platform_instance=self.config.platform_instance,
            env=self.config.env,
        )

    def _emit_table(self, table) -> Iterable[MetadataWorkUnit]:
        dataset_urn = self._make_dataset_urn(table)
        schema_metadata = self._build_schema_metadata(table)

        # Emit schema aspect
        yield MetadataChangeProposalWrapper(
            entityUrn=dataset_urn,
            aspect=schema_metadata,
        ).as_workunit()

        # ⭐ Add to resolver so SQL parsing can resolve columns later
        self.schema_resolver.add_schema_metadata(dataset_urn, schema_metadata)
```

**Key points:**

- Populate schemas **during metadata extraction**, before parsing SQL for lineage
- Pass the populated resolver to `sqlglot_lineage()` or `SqlParsingAggregator`
- Without schema info, you'll only get table-level lineage (no column mapping)

### API-Based Lineage Extraction

For sources that provide lineage information via APIs (BI tools, transformation tools):

```python
def _extract_dashboard_lineage(
    self,
    dashboard_urn: str,
    dashboard: Dict[str, Any]
) -> Iterable[MetadataWorkUnit]:
    """Extract lineage from API response"""

    # Get lineage from API
    lineage_info = self.api_client.get_dashboard_lineage(dashboard["id"])

    if not lineage_info:
        return

    # Build upstream list
    upstreams = []
    for table in lineage_info.get("tables", []):
        dataset_urn = self._resolve_table_reference(table)
        if dataset_urn:
            upstreams.append(
                UpstreamClass(
                    dataset=dataset_urn,
                    type=DatasetLineageTypeClass.TRANSFORMED,
                )
            )

    if upstreams:
        lineage = UpstreamLineageClass(upstreams=upstreams)
        yield MetadataChangeProposalWrapper(
            entityUrn=dashboard_urn,
            aspect=lineage,
        ).as_workunit()
```

### System Table-Based Lineage

Some databases store view dependencies in system tables:

```python
def _get_view_lineage_workunits(
    self,
    inspector: Inspector,
    schema: str,
    view: str
) -> Iterable[MetadataWorkUnit]:
    """Extract view lineage from database system tables"""

    try:
        # Query database-specific dependency tables
        dependencies = inspector.bind.execute(f"""
            SELECT
                referenced_schema,
                referenced_table
            FROM information_schema.view_table_usage
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
            lineage = UpstreamLineageClass(
                upstreams=[
                    UpstreamClass(
                        dataset=urn,
                        type=DatasetLineageTypeClass.TRANSFORMED,
                    )
                    for urn in upstream_urns
                ]
            )
            yield MetadataChangeProposalWrapper(
                entityUrn=view_urn,
                aspect=lineage,
            ).as_workunit()

    except Exception as e:
        self.report.report_warning(
            f"{schema}.{view}",
            f"Failed to extract view lineage: {e}"
        )
```

### Best Practices

1. **Use SQL Parsing When Available** - It provides the most accurate lineage, especially for column-level lineage
2. **Fallback to API/System Tables** - Use as a fallback or complement to SQL parsing
3. **Handle Errors Gracefully** - SQL parsing can fail on complex queries; log warnings and continue
4. **Resolve URNs Correctly** - Ensure upstream dataset URNs match those from database sources
5. **Support Incremental Lineage** - Use `auto_incremental_lineage` to preserve existing lineage

```python
from datahub.ingestion.api.incremental_lineage_helper import auto_incremental_lineage

def get_workunit_processors(self) -> List[Optional[MetadataWorkUnitProcessor]]:
    return [
        *super().get_workunit_processors(),
        # Preserve existing lineage when adding new lineage
        auto_incremental_lineage(
            self.config.incremental_lineage,
            self.ctx.graph,
        ),
    ]
```
