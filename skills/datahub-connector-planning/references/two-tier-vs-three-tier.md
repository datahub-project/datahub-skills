# Two-Tier vs Three-Tier SQL Sources

This guide helps you choose the correct base class for SQL connectors.

## Overview

DataHub provides two main base classes for SQL connectors:

| Base Class                | Hierarchy                 | Example Sources           |
| ------------------------- | ------------------------- | ------------------------- |
| `TwoTierSQLAlchemySource` | Schema → Table            | DuckDB, ClickHouse, MySQL |
| `SQLAlchemySource`        | Database → Schema → Table | PostgreSQL, Snowflake     |

## Two-Tier Sources

### When to Use

Use `TwoTierSQLAlchemySource` when:

- The source treats schemas as equivalent to databases
- There's no meaningful database layer above schemas
- `inspector.get_schema_names()` returns what you want as top-level containers

### Config Class

Must inherit from `TwoTierSQLAlchemyConfig`:

```python
from datahub.ingestion.source.sql.two_tier_sql_source import TwoTierSQLAlchemyConfig

class MySourceConfig(TwoTierSQLAlchemyConfig):
    # database_pattern is available for filtering schemas
    pass
```

### Source Class

```python
from datahub.ingestion.source.sql.two_tier_sql_source import TwoTierSQLAlchemySource

class MySourceSource(TwoTierSQLAlchemySource):
    @classmethod
    def create(cls, config_dict, ctx):
        config = MySourceConfig.parse_obj(config_dict)
        return cls(config, ctx)
```

### Container Hierarchy

```
Platform Container (urn:li:dataPlatform:mysource)
└── Schema Container (urn:li:container:schema_name)
    ├── Table Dataset
    └── View Dataset
```

### Key Methods

- `get_inspectors()` - Returns iterator of (schema_name, inspector) tuples
- `get_allowed_schemas()` - Returns list of schema names to process
- `get_db_name()` - Returns current schema being processed

## Three-Tier Sources

### When to Use

Use `SQLAlchemySource` when:

- The source has distinct database and schema layers
- You need to iterate over multiple databases
- `inspector.get_schema_names()` returns schemas WITHIN a database

### Config Class

```python
from datahub.ingestion.source.sql.sql_common import BasicSQLAlchemyConfig

class MySourceConfig(BasicSQLAlchemyConfig):
    # schema_pattern and database_pattern both available
    pass
```

### Source Class

```python
from datahub.ingestion.source.sql.sql_common import SQLAlchemySource

class MySourceSource(SQLAlchemySource):
    @classmethod
    def create(cls, config_dict, ctx):
        config = MySourceConfig.parse_obj(config_dict)
        return cls(config, ctx)
```

### Container Hierarchy

```
Platform Container (urn:li:dataPlatform:mysource)
└── Database Container (urn:li:container:database_name)
    └── Schema Container (urn:li:container:database.schema_name)
        ├── Table Dataset
        └── View Dataset
```

## Decision Tree

```
Does your source have separate database and schema concepts?
│
├── YES → Does get_schema_names() return schemas within a database?
│         │
│         ├── YES → Use SQLAlchemySource (three-tier)
│         │
│         └── NO → May need custom implementation
│
└── NO → Does get_schema_names() return what you want as top-level?
         │
         ├── YES → Use TwoTierSQLAlchemySource
         │
         └── NO → May need to override get_allowed_schemas()
```

## Common Pitfalls

### Schema Name Mismatch (Two-Tier)

Some sources return schema names in unexpected formats:

```python
# DuckDB returns: ["database_file.schema_name", ...]
# But TwoTierSQLAlchemySource expects: ["schema_name", ...]

# Solution: Override get_allowed_schemas() to extract just the schema part
def get_allowed_schemas(self, inspector):
    schemas = inspector.get_schema_names()
    # Extract schema part after the dot
    return [s.split(".")[-1] for s in schemas if self._is_allowed(s)]
```

### Database/Schema Assertion (Two-Tier)

`TwoTierSQLAlchemySource` has an assertion: `assert db_name == schema`

If your source doesn't satisfy this, you need to:

1. Override `get_inspectors()` to handle the mismatch
2. Store a mapping between expected and actual schema names
3. Override `loop_tables()` and `loop_views()` to use correct names

### Inspector Reuse

For embedded databases (DuckDB, SQLite), don't create multiple connections:

```python
def get_inspectors(self):
    # Single inspector for the whole database file
    inspector = inspect(self.engine)
    for schema in self.get_allowed_schemas(inspector):
        yield schema, inspector  # Reuse same inspector
```

## See Also

- [Testing Patterns](./testing-patterns.md) - How to test your choice
- [MCE vs MCP Formats](./mce-vs-mcp-formats.md) - Output format differences
