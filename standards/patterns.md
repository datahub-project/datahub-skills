# Common Patterns and Best Practices

This guide covers common implementation patterns, code style guidelines, and best practices for DataHub sources.

## 🔴 CRITICAL REQUIREMENTS (Read First!)

Before implementing any DataHub connector, you MUST follow these requirements:

### 1. 🔴 ALWAYS Use DataHub SDK V2 (MANDATORY for New Connectors)

**For all new connectors**, you MUST use DataHub SDK V2 classes instead of raw aspect builders.

**SDK V2 Location**: `datahub.sdk` module (https://github.com/datahub-project/datahub/tree/master/metadata-ingestion/src/datahub/sdk)

**Why SDK V2?**

1. **Cleaner Code**: Less boilerplate, more readable
2. **Type Safety**: Better IDE support and autocomplete
3. **Future-proof**: New features added to SDK V2 first
4. **Consistency**: All modern DataHub connectors use SDK V2
5. **Automatic Aspects**: SDK V2 entities emit all required aspects automatically (dataPlatformInstance, status, etc.)
6. **Proper URN Generation**: URNs are generated correctly via entity constructors

**When to use SDK V2:**

- ✅ **MANDATORY** when creating a new connector from scratch
- ✅ **MANDATORY** when adding new entity types to any connector
- ✅ **PREFERRED** when refactoring existing connectors
- ⚠️ **ACCEPTABLE** to use MCP pattern (Gen 2) for bug fixes in existing MCP-based connectors
- ❌ **NEVER** use MCE pattern (Gen 1) - it's deprecated

**Available SDK V2 Entity Classes:**

- `datahub.sdk.Dataset` - For tables, views, topics, files
- `datahub.sdk.Container` - For databases, schemas, folders, workspaces
- `datahub.sdk.DataFlow` - For pipelines, DAGs
- `datahub.sdk.DataJob` - For tasks, operators
- `datahub.sdk.Dashboard` - For BI dashboards
- `datahub.sdk.Chart` - For BI charts/visualizations
- `datahub.sdk.MLModel` - For ML models
- `datahub.sdk.MLModelGroup` - For model registries
- `datahub.sdk.Tag` - For tags

#### Dataset Creation: SDK V2 vs Old Approach

**✅ CORRECT - SDK V2 (Use This!):**

```python
from datahub.sdk import Dataset
from datahub.metadata.schema_classes import SchemaMetadataClass, SchemaField, NumberTypeClass

dataset = Dataset(
    platform="myplatform",
    name="database.schema.table",
    env="PROD"
)

# Add schema
dataset.schema_metadata = SchemaMetadataClass(
    schemaName="table",
    platform="urn:li:dataPlatform:myplatform",
    version=0,
    fields=[
        SchemaField(
            fieldPath="id",
            nativeDataType="INTEGER",
            type=NumberTypeClass()
        )
    ]
)

# Add properties
dataset.properties = DatasetPropertiesClass(
    description="My table",
    customProperties={"source": "api"}
)

# Emit
yield dataset.as_workunit()
```

**❌ WRONG - Old Approach (Don't Use for New Connectors!):**

```python
from datahub.metadata.schema_classes import DatasetSnapshotClass, MetadataChangeEventClass

# Verbose and error-prone
dataset_snapshot = DatasetSnapshotClass(
    urn=f"urn:li:dataset:(urn:li:dataPlatform:myplatform,database.schema.table,PROD)",
    aspects=[]
)

# Manually build and append aspects
dataset_snapshot.aspects.append(
    SchemaMetadataClass(
        schemaName="table",
        platform="urn:li:dataPlatform:myplatform",
        version=0,
        fields=[...]
    )
)

dataset_snapshot.aspects.append(
    DatasetPropertiesClass(
        description="My table",
        customProperties={"source": "api"}
    )
)

# Manually create MCE
mce = MetadataChangeEventClass(proposedSnapshot=dataset_snapshot)
yield MetadataWorkUnit(id=dataset_snapshot.urn, mce=mce)
```

#### Container Creation: SDK V2 vs Old Approach

**✅ CORRECT - SDK V2 (Use This!):**

```python
from datahub.sdk import Container
from datahub.emitter.mcp_builder import ContainerKey

container = Container(
    key=ContainerKey(
        platform="myplatform",
        instance="prod",
        container_path=["database", "schema"]
    ),
    name="schema",
    description="Production schema",
    sub_type="Schema"
)

# Set parent container
container.parent_container = parent_container_urn

yield container.as_workunit()
```

**❌ WRONG - Old Approach (Don't Use!):**

```python
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import ContainerPropertiesClass, ContainerClass

# Manually construct URN
container_urn = f"urn:li:container:..."

# Manually create multiple MCPs
mcp1 = MetadataChangeProposalWrapper(
    entityUrn=container_urn,
    aspect=ContainerPropertiesClass(
        name="schema",
        description="Production schema"
    )
)

mcp2 = MetadataChangeProposalWrapper(
    entityUrn=container_urn,
    aspect=ContainerClass(
        container=parent_container_urn
    )
)

yield MetadataWorkUnit(id=container_urn, mcp=mcp1)
yield MetadataWorkUnit(id=container_urn, mcp=mcp2)
```

#### Verification Checklist

Before submitting code, verify:

- [ ] Using `datahub.sdk.Dataset` (not `DatasetSnapshotClass` or manual MCPs)
- [ ] Using `datahub.sdk.Container` (not manual container MCPs)
- [ ] Using `datahub.sdk.DataFlow` and `datahub.sdk.DataJob` for pipelines
- [ ] Using `.as_workunits()` to emit entities (note: plural, returns list)
- [ ] NOT mixing SDK V2 and old approach in same connector

**Code reviews will REJECT new connectors not using SDK V2.**

#### Understanding the Evolution: MCE → MCP → SDK V2

DataHub metadata emission has evolved through three generations:

| Generation         | Pattern                                       | Status                               |
| ------------------ | --------------------------------------------- | ------------------------------------ |
| **MCE (Gen 1)**    | `MetadataChangeEvent` with bundled aspects    | ❌ DEPRECATED                        |
| **MCP (Gen 2)**    | `MetadataChangeProposalWrapper.as_workunit()` | ⚠️ LEGACY (still in many connectors) |
| **SDK V2 (Gen 3)** | `datahub.sdk.Dataset.as_workunits()`          | ✅ CURRENT STANDARD                  |

**Key differences:**

1. **MCE (Deprecated)**: Bundled all aspects into single event. Error-prone, hard to maintain.

```python
# ❌ DON'T USE - Old MCE style
mce = MetadataChangeEventClass(
    proposedSnapshot=DatasetSnapshotClass(
        urn=urn,
        aspects=[aspect1, aspect2, aspect3]  # Bundled aspects
    )
)
```

1. **MCP (Legacy)**: One aspect per MCP. Still requires manual URN construction.

```python
# ⚠️ LEGACY - MCP style (acceptable for bug fixes in existing connectors)
yield MetadataChangeProposalWrapper(
    entityUrn=urn,
    aspect=DatasetPropertiesClass(...)
).as_workunit()
yield MetadataChangeProposalWrapper(
    entityUrn=urn,
    aspect=SchemaMetadataClass(...)
).as_workunit()
```

1. **SDK V2 (Current)**: Entity-centric, handles URN and aspects automatically.

```python
# ✅ USE THIS - SDK V2 style
dataset = Dataset(
    platform="flink",
    name="catalog.database.table",
    env="PROD"
)
dataset.schema_metadata = SchemaMetadataClass(...)
dataset.properties = DatasetPropertiesClass(...)
yield from dataset.as_workunits()  # Emits all aspects correctly
```

---

### 2. ⚠️ Configuration SHOULD Be in Separate File (Strongly Recommended)

**This is strongly recommended but not an absolute blocker.** Every DataHub connector should have configuration in a separate file for maintainability and consistency:

```
src/datahub/ingestion/source/<platform_name>/
├── <platform_name>.py           # Main source implementation
├── <platform_name>_config.py    # ⚠️ REQUIRED - Config goes here!
```

**✅ CORRECT:**

```python
# duckdb_config.py - Configuration in separate file
class DuckDBConfig(BasicSQLAlchemyConfig):
    database: Optional[str] = Field(default=None)
    include_view_lineage: bool = Field(default=True)

# duckdb.py - Source implementation imports config
from datahub.ingestion.source.duckdb.duckdb_config import DuckDBConfig

@config_class(DuckDBConfig)
class DuckDBSource(SQLAlchemySource):
    config: DuckDBConfig
```

**❌ WRONG - DO NOT DO THIS:**

```python
# duckdb.py - Config in same file as source
class DuckDBConfig(BasicSQLAlchemyConfig):  # WRONG!
    database: Optional[str] = Field(default=None)

class DuckDBSource(SQLAlchemySource):  # Both in same file = WRONG!
    config: DuckDBConfig
```

**Why this is strongly recommended (but not blocking):**

1. **DataHub Convention**: MOST production DataHub sources follow this pattern
2. **Code Organization**: Separates concerns (config vs implementation)
3. **Maintainability**: Easier to find and update configuration
4. **Testing**: Simplifies unit testing of config validation
5. **Reusability**: Config can be imported by other modules

**Note**: While having config in a separate file is important for code quality, it is NOT an absolute blocker for code review. However, lack of comprehensive integration tests or presence of trivial/anti-pattern tests ARE absolute blockers.

### 2. Configuration Field Descriptions Must Be Helpful

**Configuration field descriptions should help users write recipes, not just state the obvious.**

**❌ BAD - Unhelpful descriptions:**

```python
client_email: str = Field(
    description="The Client Email which can be found in your service account's JSON Key (client_email)."
)

token: str = Field(
    description="A personal access token associated with the account."
)

include_lineage: bool = Field(
    default=True,
    description="Extract lineage."
)
```

**Why bad**: Doesn't explain format, where to find it, what permissions are needed, or why/when to use it.

**✅ GOOD - Helpful descriptions:**

```python
client_email: str = Field(
    description=(
        "Service account email (format: service-account@project.iam.gserviceaccount.com). "
        "Needs BigQuery Data Viewer and Job User roles."
    )
)

token: SecretStr = Field(
    description=(
        "Personal access token. Generate in User Settings > Access Tokens. "
        "Needs permissions to read Unity Catalog metadata and lineage."
    )
)

include_table_lineage: bool = Field(
    default=True,
    description=(
        "Extract table dependencies from Unity Catalog lineage system. "
        "Shows table/view/Delta Live Tables dependencies. "
        "Requires Unity Catalog lineage enabled. Critical for impact analysis."
    )
)

stateful_ingestion_enabled: bool = Field(
    default=False,
    description=(
        "Automatically remove deleted tables/views. "
        "Maintains catalog accuracy when objects are dropped. "
        "Enables incremental lineage/usage extraction."
    )
)

target_platform_instance: Optional[str] = Field(
    default=None,
    description=(
        "Platform instance for target warehouse (e.g., 'prod_snowflake'). "
        "Must exactly match platform_instance from warehouse ingestion. "
        "Critical for linking dbt models to upstream tables. "
        "Leave blank only if no platform_instance used for warehouse."
    )
)
```

**Good descriptions include:**

1. **What it is** - Clear explanation of the field's purpose
2. **Format/examples** - Expected format or example values (e.g., "format: user@domain.com")
3. **Where to find it** - UI location or API endpoint (e.g., "Generate in User Settings > Access Tokens")
4. **Permissions needed** - Required roles or permissions (e.g., "Needs BigQuery Data Viewer role")
5. **Why/when to use** - Impact and use cases (e.g., "Critical for impact analysis")
6. **Side effects/warnings** - Performance impact or data implications (e.g., "Increases ingestion time")
7. **Dependencies** - What else must be configured (e.g., "Must match platform_instance from warehouse ingestion")

**Practical tips:**

- Use concrete examples: "e.g., 'prod_snowflake'" not "your instance name"
- Explain consequences: "Will overwrite ownership manually set in DataHub"
- Note performance: "Increases ingestion time" or "May require additional API calls"
- Specify requirements: "Requires Unity Catalog lineage enabled"
- Link related configs: "Must match platform_instance from warehouse ingestion"

**Real examples in DataHub codebase:**

- `bigquery_v2/bigquery_config.py` (24KB config file)
- `snowflake/snowflake_config.py` (separate from source)
- `looker/looker_config.py` (separate from source)
- `fivetran/config.py` (separate from source)

**DO NOT proceed with implementation until you create a separate config file.**

---

## Related Guides

- [Main Guide](main.md) - Overview and planning
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [SQL Sources](sql.md) - For SQL database sources
- [API-Based Sources](api.md) - For REST/GraphQL API sources
- [Container Creation](containers.md) - Creating containers (databases, schemas, projects, folders)
- [Lineage Extraction](lineage.md) - Implementing lineage
- [Performance](performance.md) - Performance and memory optimization
- [Testing](testing.md) - Testing strategies
- [Registration & Documentation](registration.md) - Final steps

---

## Table of Contents

1. [File Organization](#file-organization)
2. [Import Organization](#import-organization)
3. [Configuration File Structure](#configuration-file-structure)
4. [Code Comments](#code-comments)
5. [Dependencies Management](#dependencies-management)
6. [Common Implementation Patterns](#common-implementation-patterns)
7. [Error Handling & Reporting](#error-handling--reporting)
8. [Ingestion Report Patterns](#ingestion-report-patterns)
9. [Warning and Error Reporting Style Guide](#warning-and-error-reporting-style-guide)

---

## File Organization

### Standard Source Structure

```
src/datahub/ingestion/source/<platform_name>/
├── __init__.py                      # Exports main source class
├── <platform_name>.py               # Main source implementation
├── <platform_name>_config.py        # ⚠️ REQUIRED: Config in separate file
├── <platform_name>_connection.py    # Optional: Connection config
├── <platform_name>_client.py        # Optional: API/SQL client
├── <platform_name>_queries.py       # Optional: SQL queries (recommended)
├── <platform_name>_lineage.py       # Optional: Lineage extraction
├── <platform_name>_usage.py         # Optional: Usage extraction
├── <platform_name>_report.py        # Optional: Custom reporting
└── README.md                        # Documentation
```

### Query/Request Isolation (Recommended)

Consider isolating queries and API requests in dedicated files for easier maintenance and review.

#### SQL Sources:

```python
# myplatform_queries.py
MYPLATFORM_GET_TABLES = """
SELECT table_name, table_schema
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
"""
```

#### REST API Sources:

```python
# myplatform_queries.py
ENDPOINTS = {
    "list_datasets": "/api/v2/datasets",
    "get_dataset": "/api/v2/datasets/{dataset_id}",
    "get_lineage": "/api/v2/datasets/{dataset_id}/lineage",
}
```

**Benefits:**

- **Auditability**: Review all queries/endpoints in one place
- **Testing**: Validate queries independently
- **Maintenance**: Modify queries without touching business logic

### Empty `__init__.py` Files

**Keep `__init__.py` files empty when they have no exports.** Do NOT add comments like `# This file intentionally left blank` or docstrings to otherwise empty `__init__.py` files.

```python
# ✅ GOOD: Empty __init__.py (completely empty file)

# ❌ BAD: Don't add unnecessary comments
# This file intentionally left blank.

# ❌ BAD: Don't add docstrings to empty init files
"""Package for myplatform source."""
```

If the `__init__.py` needs to export classes, only then add the necessary imports:

```python
# ✅ GOOD: __init__.py with actual exports
from datahub.ingestion.source.myplatform.myplatform import MyPlatformSource
```

### **⚠️ CRITICAL**: Configuration Must Be in Separate File

**ALWAYS** put configuration classes in a separate `<platform_name>_config.py` file:

```python
# ✅ GOOD: myplatform_config.py
class MyPlatformConfig(
    StatefulIngestionConfigBase,
    PlatformInstanceConfigMixin,
    EnvConfigMixin,
):
    api_url: str
    api_key: pydantic.SecretStr
    # ... more config
```

```python
# ❌ BAD: Don't put config in main source file
# myplatform.py
class MyPlatformSource(Source):
    class Config:  # WRONG - separate file!
        api_url: str
```

**Why separate files?**

- Easier to maintain and update configurations
- Better code organization and readability
- Follows DataHub conventions
- Simplifies testing

---

## Import Organization

### Import Order (PEP 8 Standard)

**⚠️ CRITICAL**: All imports MUST be at the top of the file unless you have a strong reason.

**Standard import order:**

```python
# 1. Standard library imports
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

# 2. Third-party imports
import pydantic
import requests
from pydantic import Field, field_validator

# 3. DataHub core imports
from datahub.configuration.common import AllowDenyPattern
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.api.decorators import capability, platform_name, SourceCapability
from datahub.ingestion.api.source import Source, SourceReport
from datahub.ingestion.api.workunit import MetadataWorkUnit

# 4. DataHub entity imports (grouped by entity type)
from datahub.metadata.schema_classes import (
    ChangeTypeClass,
    DatasetPropertiesClass,
    OwnerClass,
    OwnershipClass,
    OwnershipTypeClass,
)

# 5. Local relative imports
from .myplatform_config import MyPlatformConfig
from .myplatform_client import MyPlatformClient
```

### When to Use Late Imports

**Only use late imports (inside functions) when:**

1. **Avoiding circular dependencies**

   ```python
   def get_metadata(self):
       # Import here to avoid circular dependency
       from datahub.ingestion.source.common.subtypes import DatasetSubTypes
       return DatasetSubTypes.TABLE
   ```

2. **Optional dependencies**

   ```python
   def _import_optional_library(self):
       try:
           import optional_library  # Only imported if needed
           return optional_library
       except ImportError:
           raise ImportError("Install optional_library: pip install optional_library")
   ```

3. **Performance optimization for rarely-used code paths**

   ```python
   def debug_mode(self):
       if self.config.debug:
           import pdb  # Only import when debugging
           pdb.set_trace()
   ```

**❌ BAD**: Don't use late imports without reason

```python
def process_data(self):
    import json  # WRONG - should be at top
    return json.dumps(data)
```

---

## Configuration File Structure

### Required: Separate Config File

**File**: `<platform_name>_config.py`

```python
from typing import Optional
from pydantic import Field, SecretStr

from datahub.configuration.common import AllowDenyPattern, ConfigModel
from datahub.configuration.source_common import (
    EnvConfigMixin,
    PlatformInstanceConfigMixin,
)
from datahub.ingestion.source.state.stateful_ingestion_base import (
    StatefulIngestionConfigBase,
)


class MyPlatformConnectionConfig(ConfigModel):
    """Connection configuration for MyPlatform."""

    api_url: str = Field(description="API endpoint URL")
    api_key: SecretStr = Field(description="API authentication key")
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds"
    )


class MyPlatformConfig(
    StatefulIngestionConfigBase,
    PlatformInstanceConfigMixin,
    EnvConfigMixin,
):
    """Source configuration for MyPlatform."""

    # Connection
    connection: MyPlatformConnectionConfig

    # Filters
    database_pattern: AllowDenyPattern = Field(
        default_factory=AllowDenyPattern.allow_all,
        description="Regex patterns to filter databases"
    )

    # Feature flags
    include_lineage: bool = Field(
        default=True,
        description="Extract lineage between datasets"
    )
```

### Import Config in Main Source

```python
# myplatform.py
from .myplatform_config import MyPlatformConfig

class MyPlatformSource(Source):
    def __init__(self, config: MyPlatformConfig, ctx: PipelineContext):
        super().__init__(ctx)
        self.config = config
```

### ⚠️ CRITICAL: Follow Established Patterns Only

**DO NOT add framework-specific configuration, class attributes, or settings that are not already used by existing DataHub sources.**

Before adding any class-level configuration or framework settings (e.g., Pydantic `model_config`, SQLAlchemy `__table_args__`, Django `Meta` classes), you MUST:

1. **Search the codebase** to verify other DataHub sources use the same pattern
2. **Check base classes** - the functionality may already be provided by parent classes
3. **Ask yourself**: "Is this solving a real problem, or am I being overly defensive?"

**Example of what NOT to do:**

```python
# ❌ WRONG - Adding Pydantic configuration not used by other sources
class MyPlatformConfig(ConfigModel):
    model_config = ConfigDict(extra="forbid")  # DON'T ADD THIS

    api_url: str = Field(...)
```

**Why this is wrong:**

- Base class `ConfigModel` already handles validation behavior
- Adding `extra="forbid"` may conflict with or override parent settings
- No other DataHub sources use this pattern in their configs
- It's defensive code that adds no value

**The correct approach:**

```python
# ✅ CORRECT - Follow existing patterns, trust base classes
class MyPlatformConfig(ConfigModel):
    api_url: str = Field(...)
```

**Rule of thumb**: If you can't find at least 3 existing DataHub sources doing the same thing, don't add it.

### Pydantic Configuration Best Practices

#### Use `SecretStr` for Sensitive Fields

**Always use `SecretStr` for passwords, API keys, and other sensitive credentials.**

```python
from pydantic import SecretStr, Field

class MyPlatformConfig(ConfigModel):
    # ✅ GOOD - SecretStr for sensitive data
    password: SecretStr = Field(description="Database password")
    api_key: SecretStr = Field(description="API authentication key")
    token: SecretStr = Field(description="Access token")

    # ❌ BAD - Plain string for passwords
    password: str = Field(description="Database password")  # WRONG!
```

**Why SecretStr?**

- Prevents accidental logging of secrets
- Masks value in `__repr__` and string conversion
- Requires explicit `.get_secret_value()` to access the actual value

#### Use `AllowDenyPattern` for Filtering

**Use `AllowDenyPattern` for any pattern-based filtering of entities.**

```python
from datahub.configuration.common import AllowDenyPattern

class MyPlatformConfig(ConfigModel):
    # ✅ GOOD - AllowDenyPattern with sensible defaults
    database_pattern: AllowDenyPattern = Field(
        default_factory=AllowDenyPattern.allow_all,
        description="Regex patterns to filter databases"
    )

    table_pattern: AllowDenyPattern = Field(
        default_factory=AllowDenyPattern.allow_all,
        description="Regex patterns to filter tables"
    )

    schema_pattern: AllowDenyPattern = Field(
        default_factory=lambda: AllowDenyPattern(
            deny=["^information_schema$", "^pg_.*"]
        ),
        description="Regex patterns to filter schemas (excludes system schemas by default)"
    )
```

**Usage in source:**

```python
def _should_include_table(self, table_name: str) -> bool:
    return self.config.table_pattern.allowed(table_name)
```

#### Single Validator Per Concern

**Keep pydantic validators focused on one validation concern.**

```python
from pydantic import field_validator, model_validator

class MyPlatformConfig(ConfigModel):
    host: str
    port: int
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None

    # ✅ GOOD - Single concern: port range validation
    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v

    # ✅ GOOD - Single concern: SSL configuration consistency
    @model_validator(mode="after")
    def validate_ssl_config(self) -> "MyPlatformConfig":
        if self.ssl_enabled and not self.ssl_cert_path:
            raise ValueError("ssl_cert_path required when ssl_enabled is True")
        return self

    # ❌ BAD - Multiple concerns in one validator
    @field_validator("port")
    @classmethod
    def validate_everything(cls, v: int, info) -> int:
        # DON'T mix port validation with SSL validation
        if not (1 <= v <= 65535):
            raise ValueError("Invalid port")
        if info.data.get("ssl_enabled") and not info.data.get("ssl_cert_path"):
            raise ValueError("SSL cert required")  # WRONG: Different concern
        return v
```

#### Deprecating Configuration Fields

**Use `pydantic_removed_field` helper for deprecating fields gracefully.**

```python
from datahub.configuration.pydantic_migration_helpers import pydantic_removed_field

class MyPlatformConfig(ConfigModel):
    # Current field
    include_lineage: bool = Field(default=True, description="Extract lineage")

    # ✅ GOOD - Deprecated field with migration helper
    # Old field 'extract_lineage' was renamed to 'include_lineage'
    _extract_lineage_removed = pydantic_removed_field("extract_lineage")

    # Alternative: Deprecate with custom validator that migrates value
    @field_validator("include_lineage", mode="before")
    @classmethod
    def migrate_old_field(cls, v, info):
        # Check if old field name was used
        if "extract_lineage" in (info.data or {}):
            import warnings
            warnings.warn(
                "Config field 'extract_lineage' is deprecated, use 'include_lineage' instead",
                DeprecationWarning
            )
            return info.data["extract_lineage"]
        return v
```

#### Validation Error Messages

**Provide clear, actionable error messages in validators.**

```python
@field_validator("host_port")
@classmethod
def validate_host_port(cls, v: str) -> str:
    if ":" not in v:
        # ✅ GOOD - Actionable error message
        raise ValueError(
            f"host_port must be in 'host:port' format (e.g., 'localhost:5432'), got '{v}'"
        )
    host, port_str = v.rsplit(":", 1)
    try:
        port = int(port_str)
    except ValueError:
        # ✅ GOOD - Specific error with example
        raise ValueError(
            f"Port must be a number, got '{port_str}' in '{v}'"
        )
    return v

    # ❌ BAD - Unhelpful error message
    # raise ValueError("Invalid host_port")
```

### Quick Pydantic Checklist

| Practice                                 | Required       | Example                           |
| ---------------------------------------- | -------------- | --------------------------------- |
| `SecretStr` for secrets                  | 🔴 BLOCKER     | `password: SecretStr`             |
| `AllowDenyPattern` for filters           | 🟡 Recommended | `table_pattern: AllowDenyPattern` |
| Single concern per validator             | 🟡 Recommended | Separate validators for each rule |
| Actionable error messages                | 🟡 Recommended | Include expected format in errors |
| `pydantic_removed_field` for deprecation | 🟡 Recommended | Graceful field migration          |

---

## Code Comments

### When to Write Comments

**✅ GOOD - Write comments when:**

1. **Explaining complex business logic**

   ```python
   # Snowflake ACCESS_HISTORY only available in Enterprise Edition
   # We fall back to view definitions if access_history query fails
   if config.edition == "enterprise":
       yield from self._extract_access_history()
   ```

2. **Documenting workarounds or non-obvious behavior**

   ```python
   # API returns dates in PST, convert to UTC
   # See: https://docs.platform.com/api#timezone-handling
   timestamp = pst_timestamp.astimezone(timezone.utc)
   ```

3. **Explaining WHY, not WHAT**

   ```python
   # ✅ GOOD: Explains reasoning
   # We batch requests to avoid rate limiting (max 100 req/min)
   batched_queries = chunk_list(queries, size=10)

   # ❌ BAD: States the obvious
   # Loop through queries
   for query in queries:
       ...
   ```

4. **Documenting API limitations or edge cases**

   ```python
   # Platform API doesn't support pagination for lineage endpoints
   # Must fetch all results in single request (max 10,000 records)
   lineage_data = self.client.get_lineage(limit=10000)
   ```

**❌ BAD - Don't write comments for:**

1. **Obvious code**

   ```python
   # BAD: Comment is redundant
   # Increment counter
   counter += 1

   # BAD: Comment repeats variable name
   # Get the user name
   user_name = user.get("name")
   ```

2. **Self-explanatory function names**

   ```python
   # BAD: Function name is clear
   # Validate configuration
   def validate_config(config):
       ...
   ```

3. **Type annotations**

   ```python
   # BAD: Type annotation already documents this
   # Returns a list of datasets
   def get_datasets(self) -> List[Dataset]:
       ...
   ```

### Docstrings (Required)

Always add docstrings to classes and public methods:

```python
class MyPlatformSource(Source):
    """DataHub source for MyPlatform.

    Extracts metadata including:
    - Datasets (tables, views)
    - Lineage from view definitions
    - Usage statistics from audit logs

    Requires MyPlatform API v2.0 or higher.
    """

    def get_workunits(self) -> Iterable[MetadataWorkUnit]:
        """Extract metadata from MyPlatform and yield workunits.

        Yields:
            MetadataWorkUnit: Metadata change proposals for datasets, lineage, etc.
        """
        pass
```

---

## Dependencies Management

### Adding Dependencies to setup.py

**⚠️ CRITICAL**: When you use external libraries, ALWAYS add them to `setup.py`.

**File**: `metadata-ingestion/setup.py`

#### Where to Add Dependencies

```python
# In setup.py, find the appropriate section:

# 1. For core dependencies (always installed)
install_requires = [
    "requests>=2.28.0",
    "pydantic>=1.10.0",
    # ... existing deps
]

# 2. For source-specific dependencies (optional install)
sqlalchemy_extra = {
    "sqlalchemy-bigquery": "sqlalchemy-bigquery>=1.4.1",
    "snowflake-sqlalchemy": "snowflake-sqlalchemy>=1.4.3",
}

# 3. Add your source's dependencies
myplatform_extra = {
    "myplatform-sdk": "myplatform-sdk>=2.0.0",
    "another-lib": "another-lib>=1.5.0",
}

# 4. Register in _all_extras dict
_all_extras = {
    **sqlalchemy_extra,
    **myplatform_extra,  # Add your extra here
    # ... other extras
}
```

#### Dependency Guidelines

1. **Pin major and minor versions**

   ```python
   # ✅ GOOD: Specific version range
   "requests>=2.28.0,<3.0.0"

   # ❌ BAD: Too loose
   "requests"
   ```

2. **Avoid version conflicts**
   - Check existing dependencies before adding
   - Test installation with `pip install -e ".[myplatform]"`

3. **Document required versions**

   ````markdown
   ## Requirements

   - MyPlatform SDK 2.0.0 or higher
   - Python 3.8+

   ## Installation

   ```bash
   pip install 'acryl-datahub[myplatform]'
   ```
   ````

   ```

   ```

---

## Implementing test_connection()

The `test_connection()` method is a **user-facing feature** that validates a recipe's configuration before running a full ingestion. Users invoke it via:

- **DataHub UI**: "Test Connection" button in the ingestion setup wizard
- **CLI**: `datahub ingest -c recipe.yml --test-source-connection`

This is NOT a unit test - it's a connector capability that provides early feedback to users about their configuration.

> **Reference Implementation**: See `bigquery_v2/bigquery_test_connection.py` for a comprehensive example.

### Implementation Pattern

Implement `TestableSource` and test basic connectivity first, then each capability:

```python
from datahub.ingestion.api.source import (
    CapabilityReport,
    SourceCapability,
    TestConnectionReport,
    TestableSource,
)

class MySource(StatefulIngestionSourceBase, TestableSource):
    @staticmethod
    def test_connection(config_dict: dict) -> TestConnectionReport:
        test_report = TestConnectionReport()

        try:
            # 1. Parse config and create client
            config = MySourceConfig.parse_obj_allow_extras(config_dict)
            client = config.get_client()

            # 2. Test basic connectivity
            test_report.basic_connectivity = MySource._test_connectivity(client)

            # 3. Test each capability separately
            capability_report = {}

            capability_report[SourceCapability.SCHEMA_METADATA] = (
                MySource._test_metadata_capability(client, config)
            )

            if config.include_lineage:
                capability_report[SourceCapability.LINEAGE_COARSE] = (
                    MySource._test_lineage_capability(client, config)
                )

            test_report.capability_report = capability_report

        except Exception as e:
            test_report.basic_connectivity = CapabilityReport(
                capable=False, failure_reason=f"{e}"
            )

        return test_report

    @staticmethod
    def _test_connectivity(client) -> CapabilityReport:
        """Simple operation to verify connection works."""
        try:
            client.query("SELECT 1")
            return CapabilityReport(capable=True)
        except Exception as e:
            return CapabilityReport(capable=False, failure_reason=str(e))
```

### Key Principles

- **Test basic connectivity first** - Simple operation like `SELECT 1`
- **Test each capability independently** - Users see exactly what's working/failing
- **Return actionable error messages** - Help users fix issues without running full ingestion
- **Don't do heavy work** - This should be fast; don't scan all tables

---

## Common Implementation Patterns

### URN Generation

Use DataHub's URN builders consistently:

```python
from datahub.utilities.urns.dataset_urn import DatasetUrn
from datahub.emitter.mce_builder import (
    make_dashboard_urn,
    make_chart_urn,
    make_tag_urn,
)

# ✅ GOOD: Use URN builder
dataset_urn = DatasetUrn(
    platform="myplatform",
    name="database.schema.table",
    env=self.config.env
)

# Dashboard URN
dashboard_urn = make_dashboard_urn(
    platform="looker",
    dashboard_id="dashboard_123"
)

# ❌ BAD: Manual string concatenation
dataset_urn = f"urn:li:dataset:(urn:li:dataPlatform:myplatform,database.schema.table,{self.config.env})"
```

### Stateful Ingestion

**Enable in Config**:

```python
class MySourceConfig(StatefulIngestionConfigBase):
    stateful_ingestion: Optional[StatefulStaleMetadataRemovalConfig] = Field(
        default=None,
        description="Stateful ingestion configuration for stale entity removal"
    )
```

**Register Handlers**:

```python
from datahub.ingestion.source.state.stale_entity_removal_handler import (
    StaleEntityRemovalHandler
)

def __init__(self, config, ctx):
    super().__init__(ctx)
    self.config = config

    # Handler tracks emitted URNs and removes stale ones
    self.stale_entity_removal_handler = StaleEntityRemovalHandler.create(
        self, self.config, self.ctx
    )
```

### Pagination Pattern

```python
def _get_all_datasets(self) -> List[Dataset]:
    """Fetch all datasets with pagination."""
    all_datasets = []
    page = 1
    page_size = 100

    while True:
        response = self.client.get_datasets(page=page, page_size=page_size)
        datasets = response["data"]
        all_datasets.extend(datasets)

        logger.debug(f"Fetched page {page}: {len(datasets)} datasets")

        # Check if more pages exist
        if len(datasets) < page_size or not response.get("has_next"):
            break

        page += 1

    logger.info(f"Fetched total of {len(all_datasets)} datasets")
    return all_datasets
```

### Rate Limiting

```python
import time

class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = None

    def wait_if_needed(self):
        """Sleep if necessary to respect rate limit."""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

        self.last_request_time = time.time()
```

---

## Error Handling & Reporting

### Standard Error Handling Pattern

```python
from datahub.ingestion.api.source import SourceReport

class MyPlatformReport(SourceReport):
    """Custom report for tracking MyPlatform-specific metrics."""

    datasets_scanned: int = 0
    datasets_failed: int = 0
    api_errors: int = 0

    def report_dataset_scanned(self):
        self.datasets_scanned += 1

    def report_dataset_failed(self):
        self.datasets_failed += 1

    def report_api_error(self):
        self.api_errors += 1


class MyPlatformSource(Source):
    def __init__(self, config: MyPlatformConfig, ctx: PipelineContext):
        super().__init__(ctx)
        self.config = config
        self.report = MyPlatformReport()

    def get_workunits(self) -> Iterable[MetadataWorkUnit]:
        """Extract metadata with proper error handling."""

        for dataset_id in self._get_dataset_ids():
            try:
                # Try to process dataset
                dataset_metadata = self._get_dataset_metadata(dataset_id)
                self.report.report_dataset_scanned()

                yield self._create_workunit(dataset_metadata)

            except requests.HTTPError as e:
                # API-specific errors
                self.report.report_api_error()
                self.report.report_warning(
                    f"Failed to fetch dataset {dataset_id}",
                    context=str(e)
                )

            except Exception as e:
                # Unexpected errors
                self.report.report_dataset_failed()
                self.report.report_failure(
                    f"Unexpected error processing {dataset_id}",
                    exc=e
                )
```

### Error Reporting Best Practices

1. **Use structured reporting**

   ```python
   # ✅ GOOD: Structured with context
   self.report.report_warning(
       "Dataset missing required field",
       context=f"dataset_id={dataset.id}, field=description"
   )

   # ❌ BAD: Generic error message
   logger.warning("Error occurred")
   ```

2. **Don't fail entire ingestion on single errors**

   ```python
   # ✅ GOOD: Continue processing other datasets
   for dataset in datasets:
       try:
           yield process_dataset(dataset)
       except Exception as e:
           self.report.report_warning(f"Failed: {dataset.id}", exc=e)
           continue  # Keep going

   # ❌ BAD: Fail entire ingestion
   for dataset in datasets:
       yield process_dataset(dataset)  # Unhandled exception stops everything
   ```

3. **Provide actionable error messages**

   ```python
   # ✅ GOOD: Tells user how to fix
   raise ValueError(
       "API key is invalid. Please check your configuration at "
       "https://platform.com/settings/api-keys"
   )

   # ❌ BAD: No guidance
   raise ValueError("Invalid API key")
   ```

---

## Ingestion Report Patterns

### **⚠️ CRITICAL**: Report Files Must Be Separate

**ALWAYS** create custom report classes in a separate `<platform_name>_report.py` file for major sources:

```python
# ✅ GOOD: myplatform_report.py
from dataclasses import dataclass, field
from datahub.ingestion.source.state.stale_entity_removal_handler import (
    StaleEntityRemovalSourceReport
)

@dataclass
class MyPlatformReport(StaleEntityRemovalSourceReport):
    """Custom report for MyPlatform ingestion."""

    datasets_scanned: int = 0
    tables_scanned: int = 0
    views_scanned: int = 0

    def report_dataset_scanned(self) -> None:
        self.datasets_scanned += 1
```

```python
# ❌ BAD: Don't define report in main source file
# myplatform.py
class MyPlatformSource(Source):
    class Report(SourceReport):  # WRONG - separate file!
        datasets_scanned: int = 0
```

**Why separate files?**

- Cleaner code organization
- Easier to maintain metrics
- Better testing isolation
- Follows DataHub conventions

---

### When to Create Custom Report Classes

#### Use Base `SourceReport` When:

Simple sources with minimal tracking needs:

```python
# Simple metadata extraction only
from datahub.ingestion.api.source import Source, SourceReport

class SimpleSource(Source):
    def __init__(self, config, ctx):
        super().__init__(ctx)
        self.report = SourceReport()  # Base class is sufficient
```

**Use for**: Basic file sources, simple metadata extractors

#### Create Custom Report Class When:

Your source needs to track **any** of these:

1. **Entity counts** (tables, views, dashboards, charts scanned)
2. **Filtering/dropped entities** (which entities were filtered out)
3. **Lineage metrics** (lineage edges, parsing failures)
4. **Performance metrics** (API call counts, timing)
5. **Parsing errors** (SQL parsing failures, invalid data)
6. **Sub-reports** (separate tracking for lineage, usage, profiling)

**Use for**: All SQL sources, API sources, BI tools, data warehouses (90%+ of sources)

---

### Base Classes to Inherit From

#### 1. `StaleEntityRemovalSourceReport` (Most Common)

**Use for**: API-based sources, file sources, BI tools, NoSQL databases

**Provides**:

- `soft_deleted_stale_entities: LossyList[str]` - Tracks soft-deleted entities
- `report_stale_entity_soft_deleted(urn: str)` - Helper method
- Stateful ingestion support

**Examples**: Grafana, Looker, PowerBI, Excel, S3, MongoDB, Elasticsearch

```python
from dataclasses import dataclass
from datahub.ingestion.source.state.stale_entity_removal_handler import (
    StaleEntityRemovalSourceReport
)

@dataclass
class GrafanaSourceReport(StaleEntityRemovalSourceReport):
    dashboards_scanned: int = 0
    charts_scanned: int = 0
    panels_with_lineage: int = 0

    def report_dashboard_scanned(self) -> None:
        self.dashboards_scanned += 1
```

#### 2. `SQLSourceReport` (For SQL Sources)

**Use for**: SQL databases, data warehouses, query engines

**Provides**:

- `tables_scanned: int` - Track tables processed
- `views_scanned: int` - Track views processed
- `entities_profiled: int` - Track profiled entities
- `filtered: LossyList[str]` - Track filtered entities
- `report_entity_scanned(name, ent_type)` - Helper method
- `report_entity_profiled(name)` - Helper method
- SQL parsing metrics

**Examples**: Snowflake, BigQuery, Redshift, Teradata, Vertica

```python
from dataclasses import dataclass
from datahub.ingestion.source.sql.sql_common import SQLSourceReport

@dataclass
class MyDatabaseReport(SQLSourceReport):
    # SQLSourceReport already provides:
    # - tables_scanned, views_scanned
    # - entities_profiled
    # - filtered entities tracking

    # Add custom metrics
    stored_procedures_scanned: int = 0
    custom_objects_scanned: int = 0
```

#### 3. Multiple Inheritance (Complex Sources)

Combine multiple base classes for comprehensive tracking:

```python
from dataclasses import dataclass
from datahub.ingestion.source.sql.sql_common import SQLSourceReport
from datahub.ingestion.source.state.stateful_ingestion_base import (
    StatefulIngestionReport
)
from datahub.ingestion.source_report.time_window import BaseTimeWindowReport
from datahub.classification.classification_mixin import ClassificationReportMixin

@dataclass
class BigQueryV2Report(
    SQLSourceReport,              # SQL source basics
    BaseTimeWindowReport,          # Time window tracking
    ClassificationReportMixin,     # Classification tracking
):
    # Sub-reports
    schema_api_perf: BigQuerySchemaApiPerfReport = field(
        default_factory=BigQuerySchemaApiPerfReport
    )

    # Custom metrics
    num_usage_workunits_emitted: int = 0
    total_query_log_entries: int = 0
```

---

### Common Metrics to Track

#### A. Entity Counts (Essential)

Track how many entities were scanned:

```python
@dataclass
class MySourceReport(StaleEntityRemovalSourceReport):
    # Basic entity counts
    databases_scanned: int = 0
    schemas_scanned: int = 0
    tables_scanned: int = 0
    views_scanned: int = 0

    # BI-specific counts
    dashboards_scanned: int = 0
    charts_scanned: int = 0
    reports_scanned: int = 0
```

#### B. Filtering/Dropped Entities

Track which entities were filtered out:

```python
from datahub.utilities.lossy_collections import LossyList

@dataclass
class MySourceReport(StaleEntityRemovalSourceReport):
    # Entities filtered by patterns
    filtered_databases: LossyList[str] = field(default_factory=LossyList)
    filtered_tables: LossyList[str] = field(default_factory=LossyList)
    filtered_dashboards: LossyList[str] = field(default_factory=LossyList)

    # Entities dropped due to errors
    dropped_entities: LossyList[str] = field(default_factory=LossyList)
```

#### C. Lineage Metrics

Track lineage extraction results:

```python
from datahub.utilities.lossy_collections import LossyList, TopKDict

@dataclass
class MySourceReport(StaleEntityRemovalSourceReport):
    # Lineage counts
    num_table_to_table_edges_scanned: int = 0
    num_view_definition_parsed: int = 0

    # Lineage failures
    num_view_definitions_failed_parsing: int = 0
    view_definitions_parsing_failures: LossyList[str] = field(default_factory=LossyList)

    # SQL parser failures by type
    num_lineage_entries_sql_parser_failure: TopKDict[str, int] = field(
        default_factory=TopKDict
    )

    # Time windows (for stateful ingestion)
    lineage_start_time: Optional[datetime] = None
    lineage_end_time: Optional[datetime] = None
    stateful_lineage_ingestion_enabled: bool = False
```

#### D. Performance Metrics

Track API calls and timing:

```python
from datahub.utilities.perf_timer import PerfTimer

@dataclass
class MySourceReport(StaleEntityRemovalSourceReport):
    # API call counts
    num_list_datasets_api_requests: int = 0
    num_get_dataset_details_api_requests: int = 0

    # Performance timers
    metadata_extraction_sec: Dict[str, float] = field(default_factory=dict)
    query_parse_timer: PerfTimer = field(default_factory=PerfTimer)
    api_call_timer: PerfTimer = field(default_factory=PerfTimer)

    # Query performance
    query_secs: float = -1
```

#### E. Parsing Errors

Track parsing failures:

```python
@dataclass
class MySourceReport(StaleEntityRemovalSourceReport):
    # SQL parsing failures
    sql_parser_parse_failures: int = 0
    sql_parser_skipped_missing_code: LossyList[str] = field(default_factory=LossyList)

    # JSON/XML parsing failures
    invalid_json_responses: int = 0
    invalid_json_examples: LossyList[str] = field(default_factory=LossyList)
```

#### F. Usage Metrics

Track usage statistics extraction:

```python
@dataclass
class MySourceReport(StaleEntityRemovalSourceReport):
    # Usage counts
    num_usage_workunits_emitted: int = 0
    dashboards_scanned_for_usage: int = 0
    queries_parsed_for_usage: int = 0

    # Usage time windows
    usage_start_time: Optional[datetime] = None
    usage_end_time: Optional[datetime] = None
```

---

### Helper Methods Pattern

**ALWAYS** provide helper methods for incrementing metrics:

```python
@dataclass
class MySourceReport(StaleEntityRemovalSourceReport):
    datasets_scanned: int = 0
    datasets_failed: int = 0
    api_call_count: int = 0

    # Helper methods with clear naming
    def report_dataset_scanned(self) -> None:
        """Increment datasets scanned counter."""
        self.datasets_scanned += 1

    def report_dataset_failed(self, dataset_id: str, error: str) -> None:
        """Record dataset processing failure."""
        self.datasets_failed += 1
        self.report_warning(
            f"Failed to process dataset {dataset_id}",
            context=error
        )

    def report_api_call(self) -> None:
        """Track API call count."""
        self.api_call_count += 1
```

**Benefits**:

- Encapsulation of tracking logic
- Type safety
- Clear API for report updates
- Can add validation/logging
- Easy to mock in tests

**Naming convention**: Use `report_*` prefix for all helper methods

---

### Sub-Reports for Complex Sources

Break down complex sources into sub-reports:

```python
# bigquery_report.py

@dataclass
class BigQuerySchemaApiPerfReport:
    """Track BigQuery schema API performance."""
    list_projects: PerfTimer = field(default_factory=PerfTimer)
    list_datasets: PerfTimer = field(default_factory=PerfTimer)
    get_columns: PerfTimer = field(default_factory=PerfTimer)

@dataclass
class BigQueryAuditLogApiPerfReport:
    """Track BigQuery audit log API performance."""
    num_list_projects_api_requests: int = 0
    num_list_tables_api_requests: int = 0

@dataclass
class BigQueryV2Report(
    SQLSourceReport,
    BaseTimeWindowReport,
    ClassificationReportMixin,
):
    """Main BigQuery report with sub-reports."""

    # Sub-reports for different aspects
    schema_api_perf: BigQuerySchemaApiPerfReport = field(
        default_factory=BigQuerySchemaApiPerfReport
    )
    audit_log_api_perf: BigQueryAuditLogApiPerfReport = field(
        default_factory=BigQueryAuditLogApiPerfReport
    )

    # Main metrics
    num_usage_workunits_emitted: int = 0
    total_query_log_entries: int = 0
```

**Use sub-reports when**:

- Source has multiple distinct components (schema, lineage, usage)
- Need separate performance tracking
- Want to organize related metrics together

---

### Report Initialization

#### Pattern 1: Direct Instantiation (Recommended)

```python
# myplatform.py
from .myplatform_report import MyPlatformReport

class MyPlatformSource(Source):
    def __init__(self, config: MyPlatformConfig, ctx: PipelineContext):
        super().__init__(ctx)
        self.config = config
        self.report = MyPlatformReport()  # Direct instantiation
```

#### Pattern 2: With Initial Configuration

```python
class MyPlatformSource(Source):
    def __init__(self, config: MyPlatformConfig, ctx: PipelineContext):
        super().__init__(ctx)
        self.config = config
        self.report = MyPlatformReport()

        # Set configuration flags in report
        self.report.include_usage_stats = config.include_usage_stats
        self.report.include_lineage = config.include_lineage
```

#### Pattern 3: Field with default_factory

```python
from dataclasses import dataclass, field

@dataclass
class MyPlatformSource(Source):
    # For simple sources with base report
    report: SourceReport = field(default_factory=SourceReport)
```

---

### Common Utility Types

#### `LossyList[T]`

Stores items with a maximum limit (automatically drops oldest):

```python
from datahub.utilities.lossy_collections import LossyList

filtered_entities: LossyList[str] = field(default_factory=LossyList)
error_messages: LossyList[str] = field(default_factory=LossyList)
```

**Use for**: Unbounded lists (errors, filtered entities, warnings)

#### `LossyDict[K, V]`

Dictionary with maximum size:

```python
from datahub.utilities.lossy_collections import LossyDict

upstream_lineage: LossyDict[str, List[str]] = field(default_factory=LossyDict)
```

**Use for**: Large mappings that may grow unbounded

#### `TopKDict[K, V]`

Keeps only top K entries by value:

```python
from datahub.utilities.lossy_collections import TopKDict

# Track top parsing failures
sql_parser_failures_by_table: TopKDict[str, int] = field(
    default_factory=TopKDict
)
```

**Use for**: Performance metrics, frequency tracking

#### `PerfTimer`

Tracks elapsed time for operations:

```python
from datahub.utilities.perf_timer import PerfTimer

api_timer: PerfTimer = field(default_factory=PerfTimer)

# Usage
with self.report.api_timer:
    response = self.client.get_data()
```

**Use for**: API call timing, operation profiling

---

### Complete Examples

#### Example 1: Simple API Source Report

```python
# grafana_report.py
from dataclasses import dataclass
from datahub.ingestion.source.state.stale_entity_removal_handler import (
    StaleEntityRemovalSourceReport
)

@dataclass
class GrafanaSourceReport(StaleEntityRemovalSourceReport):
    """Ingestion report for Grafana source."""

    # Entity counts
    dashboards_scanned: int = 0
    charts_scanned: int = 0

    # Lineage tracking
    panels_with_lineage: int = 0
    panels_without_lineage: int = 0
    lineage_extraction_failures: int = 0

    # Helper methods
    def report_dashboard_scanned(self) -> None:
        self.dashboards_scanned += 1

    def report_chart_scanned(self) -> None:
        self.charts_scanned += 1

    def report_lineage_extracted(self) -> None:
        self.panels_with_lineage += 1

    def report_lineage_failed(self, panel_id: str, error: str) -> None:
        self.lineage_extraction_failures += 1
        self.report_warning(
            f"Failed to extract lineage for panel {panel_id}",
            context=error
        )
```

#### Example 2: SQL Source with Sub-Reports

```python
# snowflake_report.py
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from datahub.ingestion.source.sql.sql_common import SQLSourceReport
from datahub.ingestion.source.state.stateful_ingestion_base import (
    StatefulIngestionReport
)
from datahub.utilities.lossy_collections import LossyList, TopKDict

@dataclass
class SnowflakeUsageReport:
    """Sub-report for Snowflake usage tracking."""
    num_usage_workunits_emitted: int = 0
    usage_start_time: Optional[datetime] = None
    usage_end_time: Optional[datetime] = None

@dataclass
class SnowflakeV2Report(
    SQLSourceReport,
    StatefulIngestionReport,
):
    """Main Snowflake ingestion report."""

    # Metadata counts
    databases_scanned: int = 0
    schemas_scanned: int = 0
    tags_scanned: int = 0

    # Lineage metrics
    table_lineage_query_secs: float = -1
    num_tables_with_known_upstreams: int = 0
    num_view_definitions_parsed: int = 0
    num_view_definitions_failed_parsing: int = 0

    # Sub-reports
    usage_aggregation: SnowflakeUsageReport = field(
        default_factory=SnowflakeUsageReport
    )

    # Configuration tracking
    include_usage_stats: bool = False
    include_operational_stats: bool = False

    # Helper methods
    def report_entity_scanned(self, name: str, ent_type: str = "table") -> None:
        if ent_type == "table":
            self.tables_scanned += 1
        elif ent_type == "view":
            self.views_scanned += 1
        elif ent_type == "database":
            self.databases_scanned += 1
        elif ent_type == "schema":
            self.schemas_scanned += 1
```

---

### Best Practices Checklist

**Report Organization**:

- [ ] Report in separate `<platform>_report.py` file (for major sources)
- [ ] Inherit from appropriate base class (`StaleEntityRemovalSourceReport` or `SQLSourceReport`)
- [ ] Use `@dataclass` decorator
- [ ] All fields have type annotations

**Metrics to Track**:

- [ ] Entity counts (scanned, processed)
- [ ] Filtered/dropped entities (with `LossyList`)
- [ ] Lineage metrics (edges, parsing failures)
- [ ] Performance metrics (API calls, timing with `PerfTimer`)
- [ ] Parsing errors (with examples in `LossyList`)

**Helper Methods**:

- [ ] Provide `report_<entity>_scanned()` methods
- [ ] Provide `report_<entity>_failed()` methods with error reporting
- [ ] Use `report_*` naming convention
- [ ] Include docstrings for helper methods

**Advanced Patterns**:

- [ ] Use sub-reports for complex sources (with `field(default_factory=...)`)
- [ ] Track configuration flags that affect ingestion
- [ ] Track time windows for stateful ingestion
- [ ] Use appropriate utility types (`LossyList`, `TopKDict`, `PerfTimer`)

---

## Warning and Error Reporting Style Guide

### Overview

DataHub's `SourceReport` provides structured methods for reporting warnings and failures. Proper use of these methods helps users understand ingestion issues and take corrective action.

There are three structured log levels:

- **failure** - Fatal errors and major ingestion issues
- **warning** - Non-fatal issues that still impact ingestion run status (e.g., "Finished with warnings")
- **info** - Informational messages that can be useful but don't need to be looked at (e.g., no tables/views were found in a given schema)

### Available Methods

#### Warning Methods

```python
# Does NOT log to console by default (will be deprecated)
def report_warning(
    self,
    message: LiteralString,           # ⚠️ MUST be constant string
    context: Optional[str] = None,    # Can be dynamic (f-strings OK)
    title: Optional[LiteralString] = None,  # ⚠️ MUST be constant string
    exc: Optional[BaseException] = None,
) -> None

# DOES log to console by default (PREFERRED - use this one)
def warning(
    self,
    message: LiteralString,           # ⚠️ MUST be constant string
    context: Optional[str] = None,    # Can be dynamic (f-strings OK)
    title: Optional[LiteralString] = None,  # ⚠️ MUST be constant string
    exc: Optional[BaseException] = None,
    log: bool = True,
) -> None
```

#### Failure/Error Methods

```python
# Logs to console and adds to report
def failure(
    self,
    message: LiteralString,           # ⚠️ MUST be constant string
    context: Optional[str] = None,    # Can be dynamic (f-strings OK)
    title: Optional[LiteralString] = None,  # ⚠️ MUST be constant string
    exc: Optional[BaseException] = None,
    log: bool = True,
) -> None

# Alias (same as failure)
def report_failure(
    self,
    message: LiteralString,           # ⚠️ MUST be constant string
    context: Optional[str] = None,    # Can be dynamic (f-strings OK)
    title: Optional[LiteralString] = None,  # ⚠️ MUST be constant string
    exc: Optional[BaseException] = None,
    log: bool = True,
) -> None
```

#### Context Manager for Exception Handling

```python
with self.report.report_exc(
    title="Unable to get dataset",
    message="Error extracting dataset info from API response.",
    context=dataset_name,  # Dynamic value goes in context
    level=StructuredLogLevel.WARN
):
    # code that might throw an exception
    ...
```

**Key Differences:**

- `warning()` / `report_warning()` - Issue logged, processing continues
- `failure()` / `report_failure()` - Critical error, usually stops processing
- **Prefer `warning()` over `report_warning()`** - `warning()` also prints a log line that mirrors the warning information. `report_warning()` will eventually be deprecated.

---

### 🔴 BLOCKER: LiteralString Requirement for `title` and `message`

**The `title` and `message` parameters MUST be constant (literal) strings.** They are typed as `LiteralString` which means they must be known at compile time - no f-strings with variables, no string concatenation with variables.

#### Why This Matters

1. **Error Aggregation**: `title + message` form the top-level key for error grouping. Because these are constant strings, we should never have a large number of unique combinations. Dynamic values in `title` or `message` break aggregation and can cause memory issues.

2. **UI Display**: When `title` is not provided, the UI shows "An unexpected issue occurred". Including a constant title helps users understand the error category.

3. **Type Safety**: `LiteralString` (PEP 675) prevents SQL injection and log injection attacks by ensuring only compile-time constant strings are used.

#### ✅ CORRECT Usage

```python
# ✅ CORRECT - Constant strings for title and message, dynamic value in context
self.report.warning(
    title="Failed to extract lineage",
    message="Unable to parse view definition. Lineage will be incomplete.",
    context=f"{database}.{schema}.{view_name}",  # Dynamic values go here
    exc=e,
)

# ✅ CORRECT - Entity identifier in context
self.report.warning(
    title="Permission denied",
    message="Insufficient permissions to access table metadata.",
    context=table_name,  # Dynamic value
)

# ✅ CORRECT - Multiple dynamic values in context
self.report.warning(
    title="API rate limit exceeded",
    message="Request throttled. Will retry with backoff.",
    context=f"endpoint={endpoint}, retry_count={retry_count}",
)
```

#### ❌ INCORRECT Usage (BLOCKER)

```python
# ❌ WRONG - f-string in message (violates LiteralString)
self.report.warning(
    f"{db_name}.{schema}",  # WRONG: Dynamic value as message
    "Stored procedures not supported",
)

# ❌ WRONG - Dynamic value in title
self.report.warning(
    title=f"Failed to process {table_name}",  # WRONG: f-string in title
    message="Table will be skipped",
)

# ❌ WRONG - String concatenation in message
self.report.warning(
    title="Parse error",
    message="Failed to parse: " + view_name,  # WRONG: concatenation
)

# ❌ WRONG - Variable as message
error_msg = f"Error in {schema}"
self.report.warning(
    message=error_msg,  # WRONG: variable (not literal)
    context=schema,
)
```

#### How to Fix Common Mistakes

```python
# ❌ BEFORE (wrong)
self.report.warning(
    f"{db_name}.{schema}",
    "Stored procedures not supported in Doris",
)

# ✅ AFTER (correct)
self.report.warning(
    title="Stored procedures not supported",
    message="Doris does not support stored procedure extraction.",
    context=f"{db_name}.{schema}",
)
```

```python
# ❌ BEFORE (wrong)
self.report.warning(
    title=f"Failed to get metadata for {table_name}",
    message="Will skip this table",
)

# ✅ AFTER (correct)
self.report.warning(
    title="Failed to get table metadata",
    message="Table will be skipped due to metadata extraction failure.",
    context=table_name,
)
```

### Parameter Purposes Summary

| Parameter | Type            | Purpose                                | Dynamic Values?             |
| --------- | --------------- | -------------------------------------- | --------------------------- |
| `title`   | `LiteralString` | Short error category (2-5 words)       | ❌ NO - must be constant    |
| `message` | `LiteralString` | Detailed explanation + fix suggestions | ❌ NO - must be constant    |
| `context` | `str`           | Resource identifier, error details     | ✅ YES - use f-strings here |
| `exc`     | `BaseException` | Exception for stack trace              | N/A                         |

---

### When to Use WARNING vs FAILURE

#### Use **WARNING** when:

1. **Recoverable issues** - Ingestion can continue with partial data loss

   ```python
   # Example: Failed to extract lineage for one table
   except Exception as e:
       self.report.warning(
           title="Failed to extract lineage",
           message="Lineage for this table will be skipped",
           context=f"table={table_name}",
           exc=e,
       )
       continue  # Process next table
   ```

2. **Partial data loss** - Some metadata is missing but core data captured

   ```python
   # Example: Optional metadata field missing
   if not dataset.get("description"):
       self.report.warning(
           title="Missing description",
           message="Dataset description not available",
           context=f"dataset={dataset['name']}",
       )
   ```

3. **Parsing failures** - Individual query/view parsing fails

   ```python
   # Example: SQL parsing failed
   except SqlParseError as e:
       self.report.warning(
           title="Failed to parse SQL",
           message="Unable to extract lineage from this view definition",
           context=f"view={view_name}, sql={view_definition[:100]}",
           exc=e,
       )
   ```

4. **Non-critical timeout/performance issues**

   ```python
   # Example: M-Query parsing timeout
   self.report.warning(
       title="M-Query Parsing Timeout",
       message=f"Parsing timed out after {timeout} seconds. Lineage will not be extracted for this table.",
       context=f"table={table.name}",
   )
   ```

#### Use **FAILURE** when:

1. **Authentication/Permission errors** - Cannot access source at all

   ```python
   # Example: Invalid credentials
   except PermissionError as e:
       self.report.failure(
           title="Permission denied",
           message="Failed to access metadata. Please verify your credentials have sufficient permissions.",
           exc=e,
       )
       return None  # Cannot continue
   ```

2. **Connection failures** - Cannot connect to data source

   ```python
   # Example: Connection timeout
   except ConnectionTimeout as e:
       self.report.failure(
           title="Unable to connect",
           message="Failed to connect to database. Please verify host name and port number.",
           exc=e,
       )
       return None
   ```

3. **Configuration errors** - Invalid configuration prevents operation

   ```python
   # Example: Database doesn't exist
   except DatabaseNotFound as e:
       self.report.failure(
           title="Database does not exist",
           message="Please verify that the database exists and you have access to it.",
           context=f"database={config.database}",
           exc=e,
       )
       return None
   ```

4. **API failures** - Complete API access failure

   ```python
   # Example: Unable to get datasets
   except APIError as e:
       self.report.failure(
           title="Unable to get datasets for project",
           message="Failed to retrieve dataset list. May be permission issue.",
           context=f"project={project_id}",
           exc=e,
       )
       return None
   ```

5. **Empty results** - No data from critical operations

   ```python
   # Example: No projects found
   if not projects:
       self.report.failure(
           title="No projects found",
           message="Unable to find any projects. Please verify account permissions.",
       )
       return
   ```

---

### Parameter Usage Guide

#### 1. `title` Parameter

**Purpose**: Short, searchable error category (2-5 words)

**Format**: Title case, descriptive

**Examples from codebase:**

```python
# ✅ GOOD titles
title="Unable to connect"
title="Permission denied"
title="Failed to parse SQL"
title="Missing description"
title="API Timeout"
title="Metadata API Timeout"
title="External URL Generation Failed"
title="Unable to fetch dataset details"

# ❌ BAD titles
title="Error"  # Too generic
title="Failed to connect to Snowflake database at host xyz with user abc"  # Too long
title="error processing table"  # Not title case
```

#### 2. `message` Parameter

**Purpose**: Detailed explanation with actionable guidance

**Format**: Complete sentence(s) explaining what went wrong and how to fix it

**Examples from codebase:**

```python
# ✅ GOOD messages - Actionable
message="Failed to connect to Redshift. Please verify your username, password, and database."
message="Maybe resourcemanager.projects.get permission is missing. You can assign predefined roles/bigquery.metadataViewer role to your service account."
message="Metadata endpoints are not reachable. Check network connectivity to PowerBI Service."
message="Skipping this dataset due to the error. Metadata will be incomplete."

# ❌ BAD messages - Not actionable
message="Error occurred"
message="Something went wrong"
message="Failed"
```

#### 3. `context` Parameter

**Purpose**: Specific identifiers to locate the issue

**Format**: Entity identifiers, key-value pairs for multiple details

**Common patterns:**

```python
# Single entity
context=project_id
context=table_name
context=f"dataset={dataset_id}"

# Hierarchical entities
context=f"{project_id}.{dataset_name}"
context=f"{project_id}.{dataset_name}.{table_name}"
context=f"{database}.{schema}.{table}"

# Multiple details (key=value format)
context=f"workspace={workspace.name}, dataset-id={dataset_id}"
context=f"table-name={table.full_name}, error={error_type}"
context=f"report-name: {report.name} and dataset-id: {report.dataset_id}"

# Query context
context=f"Query: '{query}'"

# URL/API context
context=f"url={url}"
```

#### 4. `exc` Parameter

**Purpose**: Include exception for debugging

**When to use**: **ALWAYS** when inside an exception handler

**Example:**

```python
try:
    result = process_entity(entity)
except Exception as e:
    self.report.warning(
        title="Failed to process entity",
        message="Entity will be skipped",
        context=f"entity={entity.id}",
        exc=e,  # ✅ Always include exception
    )
```

**Benefits of `exc` parameter:**

- Automatically adds exception type and message
- Logs full stack trace in DEBUG mode
- Helps with debugging production issues

---

### Message Formatting Examples

#### Example 1: Permission Error (Failure)

```python
# Redshift permission denied
try:
    result = query_system_table()
except PermissionError as e:
    self.report.failure(
        title="Permission denied",
        message="Failed to extract metadata due to insufficient permission to access 'svv_table_info' table. Please ensure the provided database user has access.",
        exc=e,
    )
    return None
```

#### Example 2: API Timeout (Warning)

```python
# PowerBI API timeout
try:
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
except requests.Timeout:
    self.report.warning(
        title="Metadata API Timeout",
        message="Metadata endpoints are not reachable. Check network connectivity to PowerBI Service.",
        context=f"url={api_url}",
    )
```

#### Example 3: Parsing Failure (Warning)

```python
# SQL parsing failure
try:
    parsed_lineage = parse_sql(view_definition)
except SqlParseError as e:
    self.report.warning(
        title="Failed to parse SQL",
        message="Unable to extract lineage from view definition. View lineage will be skipped.",
        context=f"view={schema}.{view_name}",
        exc=e,
    )
    continue  # Continue with next view
```

#### Example 4: Missing Data (Warning)

```python
# Missing optional metadata
if not table_details.get("description"):
    self.report.warning(
        title="Missing description",
        message="Table description not available from API. Table will be ingested without description.",
        context=f"table={project}.{dataset}.{table}",
    )
```

#### Example 5: Connection Failure (Failure)

```python
# BigQuery connection failure
try:
    projects = client.list_projects()
except GoogleAPIError as e:
    self.report.failure(
        title="Failed to get BigQuery Projects",
        message="Maybe resourcemanager.projects.get permission is missing for the service account. You can assign predefined roles/bigquery.metadataViewer role.",
        exc=e,
    )
    return None
```

---

### Continue vs Stop Pattern

#### Continue on Warnings (Recommended)

```python
# Pattern: Log warning and continue processing
for table in tables:
    try:
        metadata = extract_metadata(table)
        yield create_workunit(metadata)
    except Exception as e:
        # Log warning but continue with next table
        self.report.warning(
            title="Failed to process table",
            message="Table will be skipped. Other tables will be processed.",
            context=f"table={table.name}",
            exc=e,
        )
        continue  # ✅ Continue with next item
```

#### Stop on Failures

```python
# Pattern: Log failure and stop processing
try:
    connection = create_connection(config)
except ConnectionError as e:
    # Cannot proceed without connection
    self.report.failure(
        title="Unable to connect",
        message="Failed to establish database connection. Cannot proceed with ingestion.",
        exc=e,
    )
    return None  # ✅ Stop processing
```

---

### Best Practices

1. **Always provide `title`**
   - Makes errors searchable and groupable
   - Keep it short (2-5 words)
   - Use Title Case

2. **Always provide actionable `message`**
   - Explain what went wrong
   - Suggest how to fix it
   - Include relevant links if helpful

3. **Always provide `context`**
   - Include entity identifiers
   - Use key=value format for multiple details
   - Helps user locate the problematic entity

4. **Always include `exc` when available**
   - Inside exception handlers, always pass the exception
   - Provides stack trace for debugging

5. **Use `warning()` over `report_warning()`**
   - `warning()` logs to console (visible to user)
   - `report_warning()` only adds to report (not visible)
   - Most cases should use `warning()`

6. **Continue on warnings, stop on failures**
   - Warnings: Process remaining items
   - Failures: Return early when cannot proceed

7. **Use structured context**
   - Format: `key=value, key2=value2`
   - Example: `context=f"project={proj}, dataset={ds}"`

8. **Be specific in messages**
   - ✅ "Unable to parse view definition. Lineage will not be extracted."
   - ❌ "Parse error"

9. **Suggest solutions**
   - ✅ "Please verify your credentials have sufficient permissions"
   - ❌ "Permission denied"

10. **Track warning/failure counts**
    - Add metrics to your report class
    - Example: `api_errors: int = 0`
    - Increment in helper methods

---

### Complete Example

```python
class MyPlatformSource(Source):
    def __init__(self, config: MyPlatformConfig, ctx: PipelineContext):
        super().__init__(ctx)
        self.config = config
        self.report = MyPlatformReport()

    def get_workunits(self) -> Iterable[MetadataWorkUnit]:
        """Extract metadata with proper error handling."""

        # Critical error - stop processing
        try:
            connection = self._create_connection()
        except AuthenticationError as e:
            self.report.failure(
                title="Authentication failed",
                message="Invalid API key. Please check your configuration and verify the API key is valid.",
                exc=e,
            )
            return  # Stop processing

        # Get datasets - continue on individual failures
        for dataset_id in self._list_datasets():
            try:
                # Extract dataset metadata
                dataset = self._get_dataset(dataset_id)
                self.report.report_dataset_scanned()

                # Extract lineage - warn if fails but continue
                try:
                    lineage = self._extract_lineage(dataset)
                except ParseError as e:
                    self.report.warning(
                        title="Failed to extract lineage",
                        message="Lineage extraction failed. Dataset metadata will be ingested without lineage.",
                        context=f"dataset={dataset.name}",
                        exc=e,
                    )
                    lineage = None  # Continue without lineage

                yield self._create_workunit(dataset, lineage)

            except requests.HTTPError as e:
                # Non-critical API error - log and continue
                self.report.warning(
                    title="Failed to fetch dataset",
                    message="Dataset will be skipped. Other datasets will be processed.",
                    context=f"dataset_id={dataset_id}",
                    exc=e,
                )
                continue  # Continue with next dataset
```

---

### Quick Reference

**Choose the right method:**

- `self.report.warning()` - Recoverable issue, continue processing ✅
- `self.report.failure()` - Critical error, stop processing ✅

**Always include:**

- `title` - Short error category (2-5 words)
- `message` - Actionable explanation
- `context` - Entity identifiers (key=value format)
- `exc` - Exception object (when in exception handler)

**Pattern:**

```python
except SomeError as e:
    self.report.warning(  # or failure
        title="Short Error Category",
        message="Detailed explanation with suggested fix.",
        context=f"entity={entity_id}, detail={detail}",
        exc=e,
    )
```

---

## Quick Reference Checklist

**File Organization**:

- [ ] Configuration in separate `<platform>_config.py` file
- [ ] Report in separate `<platform>_report.py` file (for major sources)
- [ ] Imports organized at top of file (standard lib → third-party → DataHub → local)
- [ ] Only comments when they add value (explain WHY, not WHAT)

**Dependencies**:

- [ ] Dependencies added to `setup.py`
- [ ] Version ranges specified
- [ ] Installation tested

**Implementation**:

- [ ] Proper error handling with structured reporting
- [ ] URN builders used (not manual strings)
- [ ] Pagination implemented for large datasets
- [ ] Rate limiting if API has limits
- [ ] Docstrings on all classes and public methods

**Report (see [Ingestion Report Patterns](#ingestion-report-patterns))**:

- [ ] Custom report class created in separate file
- [ ] Inherits from appropriate base class (`StaleEntityRemovalSourceReport` or `SQLSourceReport`)
- [ ] Entity counts tracked (scanned, processed, dropped)
- [ ] Helper methods provided (`report_<entity>_scanned()`, `report_<entity>_failed()`)
- [ ] Use `LossyList` for unbounded lists (errors, filtered entities)
- [ ] Use `PerfTimer` for performance tracking
- [ ] Sub-reports for complex sources (if needed)

**Testing** (see [testing.md](testing.md)):

- [ ] Unit tests for logic only (not default values)
- [ ] Integration tests with golden files (end-to-end)
- [ ] Tests in separate directory under `tests/unit/<platform>` and `tests/integration/<platform>`
