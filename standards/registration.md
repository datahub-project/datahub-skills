# Registration & Documentation Guide

This guide covers the final steps: registering your source and creating documentation.

## Related Guides

- [Main Guide](main.md) - Overview and quick start
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [SQL Sources](sql.md) - For SQL database sources
- [API-Based Sources](api.md) - For REST/GraphQL API sources
- [Common Patterns](patterns.md) - Shared patterns and utilities
- [Lineage Extraction](lineage.md) - Implementing lineage
- [Performance](performance.md) - Performance and memory optimization
- [Testing](testing.md) - Testing strategies

## Registration & Documentation

### Documentation Structure

**IMPORTANT**: All source documentation must be placed in the `docs/sources/<platform_name>/` directory following this standard structure:

```
docs/sources/<platform_name>/
├── <platform>.md              # Main documentation file
└── <platform>_recipe.yml      # Recipe file with all options commented
```

**Required Files:**

1. **`<platform>.md`** - Main documentation file containing:
   - Overview and capabilities
   - Prerequisites
   - **Required Permissions** section with:
     - Minimum required permissions for basic functionality
     - Permissions organized by capability (matching `@capability` decorators)
     - Clear indication of which permissions are needed for optional features
   - Configuration tables with "Required Permission" column
   - Troubleshooting guidance
   - References to official documentation

🔴 **BLOCKER - Prerequisites Anti-Patterns:**

Prerequisites documentation must focus on **source system requirements**, NOT Python package information:

**❌ DO NOT include:**

- Python package names or versions (e.g., "requires pymysql>=1.0.0")
- SQLAlchemy version requirements
- Any dependency that's handled by `pip install acryl-datahub[source]`

**✅ DO include:**

- Required database/API permissions (e.g., `GRANT SELECT ON ...`)
- Source system version compatibility (e.g., "Doris 2.0+ recommended")
- Network/connectivity requirements (e.g., "Port 9030 for Doris FE")
- Authentication setup (e.g., "AWS IAM auth configuration")
- Known limitations of the source system

**Rationale:** Python dependencies are managed by `setup.py` and installed automatically. Duplicating them in docs creates maintenance burden and can become outdated. Users don't need to know internal package dependencies.

1. **`<platform>_recipe.yml`** - Recipe file containing:
   - All configuration options with inline comments
   - Comments explaining what each option does
   - Required vs optional indicators
   - Default values
   - Permission requirements for each feature/capability
   - Environment variable usage examples
   - Grouped configuration sections

**Example Structure:**

```text
docs/sources/db2/
├── db2.md              # Main documentation with permissions per capability
└── db2_recipe.yml      # Recipe file with all options commented
```

Both files must include:

- ✅ Permissions documentation organized by capability
- ✅ Commented configuration examples
- ✅ References to official documentation (where applicable)
- ✅ Troubleshooting guidance

### 1. Source Registry

Sources are auto-discovered via decorators. Ensure proper registration:

```python
@platform_name("MyDatabase")  # User-facing name
@config_class(MyDatabaseConfig)  # Links config
@support_status(SupportStatus.INCUBATING)  # TESTING -> INCUBATING -> CERTIFIED
@capability(SourceCapability.PLATFORM_INSTANCE, "Enabled by default")
@capability(SourceCapability.DOMAINS, "Enabled by default")
class MyDatabaseSource(SQLAlchemySource):
    pass
```

### 2. Entry Point Registration in setup.py

**File**: `metadata-ingestion/setup.py`

#### A. Source Registration

Sources are registered in the `entry_points` dictionary under `"datahub.ingestion.source.plugins"`:

**Format**:

```python
"source-name = package.module.path:SourceClassName"
```

**Location in setup.py**: Lines ~810-899 (entry_points section)

**Examples from existing sources**:

```python
entry_points={
    "datahub.ingestion.source.plugins": [
        # SQL databases
        "snowflake = datahub.ingestion.source.snowflake.snowflake_v2:SnowflakeV2Source",
        "bigquery = datahub.ingestion.source.bigquery_v2.bigquery:BigqueryV2Source",
        "redshift = datahub.ingestion.source.redshift.redshift:RedshiftSource",

        # BI tools
        "looker = datahub.ingestion.source.looker.looker_source:LookerDashboardSource",
        "powerbi = datahub.ingestion.source.powerbi.powerbi:PowerBiDashboardSource",
        "tableau = datahub.ingestion.source.tableau.tableau:TableauSource",

        # Data lakes
        "s3 = datahub.ingestion.source.s3.source:S3Source",
        "delta-lake = datahub.ingestion.source.delta_lake.source:DeltaLakeSource",
    ],
}
```

**Naming Conventions**:

- Entry name: lowercase with hyphens (e.g., `"power-bi"`, `"delta-lake"`)
- Module path: Python package structure with underscores (e.g., `power_bi`, `delta_lake`)
- Class name: CamelCase ending with `Source` (e.g., `PowerBiDashboardSource`)

#### B. Dependency Management

**Location in setup.py**: Lines ~408-619 (plugins dictionary)

Dependencies are defined in the `plugins` dictionary, which maps source names to dependency sets.

##### Pattern 1: Simple Dependencies

```python
# Define dependency set (lines 369-372)
slack = {
    "slack-sdk==3.18.1",
    "tenacity>=8.0.1",
}

# Register in plugins dict (line 582)
plugins = {
    "slack": slack,
}
```

##### Pattern 2: Using Common Dependencies

DataHub defines reusable dependency sets for common requirements:

**Available Common Sets**:

```python
# SQL sources (lines 150-177)
sql_common = (
    {
        *sqlalchemy_lib,
        *great_expectations_lib,
        "scipy>=1.7.2",
        "greenlet",
    }
    | usage_common
    | sqlglot_lib
    | classification_lib
)

# REST/API sources (line 60)
rest_common = {"requests", "requests_file"}

# AWS-based sources (lines 179-185)
aws_common = {
    "boto3",
    "botocore!=1.23.0",
}

# SQL parsing for lineage (lines 93-99)
sqlglot_lib = {
    "sqlglot>=25.25.1",
}

# Usage extraction (lines 89-91)
usage_common = sqlglot_lib

# Classification (lines 135-143)
classification_lib = {
    "libcst~=1.4",
    "pydantic-settings>=2.0.0",
}

# SQLAlchemy (lines 145-148)
sqlalchemy_lib = {
    "sqlalchemy>=1.4.39, <2",
}
```

**Example: Snowflake using common sets** (line 576):

```python
plugins = {
    "snowflake": snowflake_common | sql_common | usage_common | sqlglot_lib,
}
```

Where `snowflake_common` is defined (lines 237-263):

```python
snowflake_common = {
    # Snowflake connector
    "snowflake-connector-python>=2.8.0,<4",
    # avoid https://github.com/snowflakedb/snowflake-connector-python/issues/1847
    "pyOpenSSL~=24.1.0",
    # SQLAlchemy support
    "snowflake-sqlalchemy>=1.4.3, <1.7.4",
    # Cryptography
    "cryptography>=39.0.1; python_version < '3.12'",
    # For Python 3.12+ compatibility
    "cryptography!=42.0.0,!=42.0.1,>=42.0.2; python_version >= '3.12'",
}
```

##### Pattern 3: Combining Multiple Sets with Inline Dependencies

**BigQuery example** (lines 453-459):

```python
plugins = {
    "bigquery": sql_common
        | bigquery_common
        | sqlglot_lib
        | classification_lib
        | {
            # Inline dependencies specific to BigQuery
            "google-cloud-datacatalog-lineage==0.2.2",
        },
}
```

**PowerBI example** (lines 597-602):

```python
plugins = {
    "powerbi": (
        microsoft_common
        | {"lark[regex]==1.1.4", "sqlparse", "more-itertools"}
        | sqlglot_lib
        | threading_timeout_common
    ),
}
```

##### Pattern 4: Multi-Variant Sources

Create multiple installation options for the same source:

**Snowflake variants** (lines 576-579):

```python
plugins = {
    "snowflake": snowflake_common | sql_common | usage_common | sqlglot_lib,  # Full
    "snowflake-slim": snowflake_common,  # Minimal - just connector
    "snowflake-summary": snowflake_common | sql_common | usage_common | sqlglot_lib,
    "snowflake-queries": snowflake_common | sql_common | usage_common | sqlglot_lib,
}
```

**BigQuery variants** (lines 453-461):

```python
plugins = {
    "bigquery": sql_common | bigquery_common | sqlglot_lib | classification_lib | {...},
    "bigquery-slim": bigquery_common,  # Minimal - just Google client
    "bigquery-queries": sql_common | bigquery_common | sqlglot_lib,
}
```

**S3 variants** (lines 570-571):

```python
plugins = {
    "s3": {*s3_base, *data_lake_profiling},  # With PySpark for profiling
    "s3-slim": {*s3_base},  # Without PySpark - lightweight
}
```

**When to create variants**:

- `-slim`: Minimal dependencies for basic metadata extraction
- Full variant: Includes profiling, lineage, usage extraction
- Feature-specific variants: For specific capabilities (e.g., `-queries` for query logs)

##### Pattern 5: Empty Dependencies

Some sources don't require external dependencies:

```python
plugins = {
    "datahub-lineage-file": set(),
    "datahub-business-glossary": set(),
    "azure-ad": set(),
}
```

#### C. Version Pinning Guidelines

**Exact version** (when specific version required):

```python
"slack-sdk==3.18.1"
```

**Minimum version** (most common):

```python
"looker-sdk>=23.0.0"
```

**Version range**:

```python
"snowflake-connector-python>=2.8.0,<4"
"sqlalchemy>=1.4.39, <2"
```

**Excluding specific versions**:

```python
"botocore!=1.23.0"  # Known bug in this version
"tenacity!=8.4.0"  # Conflicts with other packages
```

**Complex constraints**:

```python
# Platform-specific constraints
"deltalake>=0.6.3, != 0.6.4, != 0.18.0, <1.0.0; platform_system == 'Darwin' and platform_machine == 'arm64'"

# Python version-specific
"cryptography>=39.0.1; python_version < '3.12'"
"cryptography!=42.0.0,!=42.0.1,>=42.0.2; python_version >= '3.12'"
```

**Best practices**:

- Use `>=` for minimum version requirements
- Use `<` to prevent breaking changes (e.g., `<2` to stay on v1.x)
- Use `!=` to exclude specific broken versions
- Add comments explaining version constraints

#### D. Complete Example: New Source Registration

```python
# Step 1: Define source-specific dependencies
myplatform_common = {
    "myplatform-sdk>=2.0.0,<3.0.0",  # Main SDK
    "python-dateutil>=2.8.0",  # Date parsing
    "tenacity>=8.0.1",  # Retry logic
}

# Step 2: Register in plugins dict
plugins = {
    # Full variant with all features
    "myplatform": rest_common | myplatform_common | sqlglot_lib,

    # Slim variant for basic metadata only
    "myplatform-slim": myplatform_common,
}

# Step 3: Register entry point
entry_points={
    "datahub.ingestion.source.plugins": [
        "myplatform = datahub.ingestion.source.myplatform.myplatform:MyPlatformSource",
    ],
}
```

#### E. Framework Dependencies

All plugins automatically get `framework_common` dependencies added (lines 1009-1012):

```python
extras_require={
    **{
        plugin: list(framework_common | dependencies)
        for (plugin, dependencies) in plugins.items()
    },
}
```

`framework_common` includes DataHub core dependencies that all sources need.

#### F. Installation After Registration

**Install your source**:

```bash
# Full variant
pip install 'acryl-datahub[myplatform]'

# Slim variant
pip install 'acryl-datahub[myplatform-slim]'

# Development install
cd metadata-ingestion
pip install -e ".[myplatform]"
```

#### G. Testing Setup.py Changes

After modifying setup.py:

```bash
# 1. Install in development mode
cd metadata-ingestion
pip install -e ".[myplatform]"

# 2. Verify entry point registration
python -c "from pkg_resources import iter_entry_points; print([ep.name for ep in iter_entry_points('datahub.ingestion.source.plugins')])"

# 3. Test source instantiation
datahub check plugins

# 4. Run your source
datahub ingest -c myplatform_recipe.yml
```

#### H. Common Mistakes to Avoid

❌ **Don't forget to add dependencies to setup.py**

```python
# If you import a package, add it to setup.py
import my_new_package  # Must be in plugins dict!
```

❌ **Don't use underscores in entry point names**

```python
# Bad
"my_platform = ..."

# Good
"my-platform = ..."
```

❌ **Don't pin versions too tightly without reason**

```python
# Bad - overly restrictive
"requests==2.28.1"

# Good - allows patch updates
"requests>=2.28.0,<3.0.0"
```

❌ **Don't forget version ranges for major dependencies**

```python
# Bad - will break on major version updates
"sqlalchemy>=1.4.39"

# Good - protects from breaking changes
"sqlalchemy>=1.4.39, <2"
```

#### I. Quick Reference

**Basic source with REST API**:

```python
plugins = {
    "mysource": rest_common | {"mysource-sdk>=1.0.0"},
}
```

**SQL source**:

```python
plugins = {
    "mysqldb": sql_common | {"mysqldb-connector>=2.0.0"},
}
```

**Source with lineage**:

```python
plugins = {
    "mysource": rest_common | sqlglot_lib | {"mysource-sdk>=1.0.0"},
}
```

**Source with variants**:

```python
plugins = {
    "mysource": rest_common | sqlglot_lib | mysource_common,
    "mysource-slim": mysource_common,
}
```

#### J. Pydantic v2 Patterns

**CRITICAL**: DataHub uses Pydantic v2. Always use v2 methods, not deprecated v1 methods.

##### Migration Guide: v1 → v2

| **Pydantic v1 (❌ DEPRECATED)** | **Pydantic v2 (✅ USE THIS)**             | **Purpose**           |
| ------------------------------- | ----------------------------------------- | --------------------- |
| `Model.parse_obj(dict)`         | `Model.model_validate(dict)`              | Parse dict to model   |
| `model.dict()`                  | `model.model_dump()`                      | Serialize to dict     |
| `model.json()`                  | `model.model_dump_json()`                 | Serialize to JSON     |
| `@validator('field')`           | `@field_validator('field', mode='after')` | Validate single field |
| `@root_validator`               | `@model_validator(mode='before/after')`   | Validate whole model  |
| `class Config:`                 | `model_config = ConfigDict(...)`          | Model configuration   |

##### 1. Parsing and Serialization

**Parse dictionary to model** (replaces `parse_obj`):

```python
# ❌ OLD - Don't use
config = MyConfig.parse_obj(config_dict)

# ✅ NEW - Use this
config = MyConfig.model_validate(config_dict)
```

**Real DataHub example**:

```python
# From datahub/lite/duckdb_lite.py
@classmethod
def create(cls, config_dict: dict) -> "DuckDBLite":
    config: DuckDBLiteConfig = DuckDBLiteConfig.model_validate(config_dict)
    return DuckDBLite(config)
```

**Serialize to dictionary** (replaces `dict()`):

```python
# ❌ OLD - Don't use
config_dict = my_config.dict()
config_dict = my_config.dict(exclude_none=True)

# ✅ NEW - Use this
config_dict = my_config.model_dump()
config_dict = my_config.model_dump(exclude_none=True)
```

**Real DataHub example**:

```python
# From datahub/ingestion/run/pipeline_config.py
def get_raw_dict(self) -> Dict:
    result = self._raw_dict
    if result is None:
        result = self.model_dump()
    return result
```

**Serialize to JSON** (replaces `json()`):

```python
# ❌ OLD - Don't use
json_str = my_config.json()

# ✅ NEW - Use this
json_str = my_config.model_dump_json()
```

##### 2. Model Configuration

**Old Config class → New ConfigDict**:

```python
# ❌ OLD - Don't use
from pydantic import BaseModel

class MyConfig(BaseModel):
    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True

# ✅ NEW - Use this
from pydantic import BaseModel, ConfigDict

class MyConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )
```

**Real DataHub example**:

```python
# From datahub/configuration/common.py
class ConfigModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        ignored_types=(cached_property,),
        json_schema_extra=_config_model_schema_extra,
        hide_input_in_errors=not get_debug(),
    )
```

**Common model_config options**:

```python
model_config = ConfigDict(
    extra="forbid",              # Don't allow extra fields
    arbitrary_types_allowed=True, # Allow non-Pydantic types
    populate_by_name=True,       # Allow field aliases
    validate_default=True,       # Validate default values
)
```

##### 3. Field Validators

**Old @validator → New @field_validator**:

```python
# ❌ OLD - Don't use
from pydantic import validator

@validator('field_name')
def validate_field(cls, v):
    if not v:
        raise ValueError("Field is required")
    return v

# ✅ NEW - Use this
from pydantic import field_validator

@field_validator('field_name', mode='after')
@classmethod
def validate_field(cls, v):
    if not v:
        raise ValueError("Field is required")
    return v
```

**Real DataHub examples**:

**Simple validation**:

```python
# From datahub/ingestion/source/snowflake/snowflake_config.py
@field_validator("convert_urns_to_lowercase", mode="after")
@classmethod
def validate_convert_urns_to_lowercase(cls, v):
    if not v:
        add_global_warning(
            "Please use `convert_urns_to_lowercase: True`, "
            "otherwise lineage to other sources may not work correctly."
        )
    return v
```

**Accessing other fields with ValidationInfo**:

```python
from pydantic import ValidationInfo

@field_validator("include_column_lineage", mode="after")
@classmethod
def validate_include_column_lineage(cls, v, info: ValidationInfo):
    # Access other fields using info.data
    if not info.data.get("include_table_lineage") and v:
        raise ValueError(
            "include_table_lineage must be True for include_column_lineage to be set."
        )
    return v
```

**Regex validation**:

```python
# From datahub/ingestion/source/bigquery_v2/bigquery_config.py
@field_validator("sharded_table_pattern", mode="after")
@classmethod
def sharded_table_pattern_is_a_valid_regexp(cls, v: str) -> str:
    try:
        re.compile(v)
    except Exception as e:
        raise ValueError(
            "sharded_table_pattern configuration pattern is invalid."
        ) from e
    return v
```

**Mode options**:

- `mode="before"`: Validate raw input before parsing
- `mode="after"`: Validate parsed value (most common)
- `mode="wrap"`: Advanced - wraps the validation process

##### 4. Model Validators

**Old @root_validator → New @model_validator**:

```python
# ❌ OLD - Don't use
from pydantic import root_validator

@root_validator
def validate_model(cls, values):
    # values is a dict
    return values

# ✅ NEW - Use this (before mode)
from pydantic import model_validator

@model_validator(mode='before')
@classmethod
def validate_model_before(cls, values: Dict[str, Any]) -> Dict[str, Any]:
    # values is still a dict (before parsing)
    return values

# ✅ NEW - Use this (after mode)
@model_validator(mode='after')
def validate_model_after(self) -> Self:
    # self is the model instance (after parsing)
    return self
```

**Real DataHub examples**:

**Mode "before" - dict-based validation**:

```python
# From datahub/ingestion/source/sql/sql_config.py
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

**Mode "after" - instance-based validation**:

```python
# From datahub/ingestion/source/sql/sql_config.py
@model_validator(mode="after")
def ensure_profiling_pattern_is_passed_to_profiling(self):
    profiling = self.profiling
    if (
        profiling is not None
        and isinstance(profiling, GEProfilingConfig)
        and profiling.enabled
    ):
        profiling._allow_deny_patterns = self.profile_pattern
    return self
```

**Complex validation with instance access**:

```python
# From datahub/ingestion/source/snowflake/snowflake_config.py
@model_validator(mode="after")
def validate_legacy_schema_pattern(self) -> "SnowflakeFilterConfig":
    schema_pattern: Optional[AllowDenyPattern] = self.schema_pattern

    if (
        schema_pattern is not None
        and schema_pattern != AllowDenyPattern.allow_all()
        and not self.match_fully_qualified_names
    ):
        logger.warning("Please update schema_pattern...")

    # Modify pattern
    if schema_pattern:
        logger.debug("Adding deny for INFORMATION_SCHEMA to schema_pattern.")
        schema_pattern.deny.append(r".*INFORMATION_SCHEMA$")

    return self
```

##### 5. Complete Configuration Example

```python
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator, ValidationInfo

class MyPlatformConfig(BaseModel):
    """Configuration for MyPlatform source."""

    # Model configuration using ConfigDict
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    # Fields with descriptions
    api_url: str = Field(description="API endpoint URL")
    api_key: SecretStr = Field(description="API key for authentication")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    enable_lineage: bool = Field(default=True, description="Extract lineage")

    # Field validator
    @field_validator("timeout", mode="after")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("timeout must be positive")
        return v

    # Field validator with access to other fields
    @field_validator("enable_lineage", mode="after")
    @classmethod
    def validate_lineage(cls, v: bool, info: ValidationInfo) -> bool:
        api_url = info.data.get("api_url", "")
        if v and "v1" in api_url:
            raise ValueError("Lineage requires API v2 or higher")
        return v

    # Model validator (before mode)
    @model_validator(mode="before")
    @classmethod
    def apply_defaults(cls, values: dict) -> dict:
        # Set timeout based on other values
        if "timeout" not in values and values.get("enable_lineage"):
            values["timeout"] = 60  # Longer timeout for lineage
        return values

    # Model validator (after mode)
    @model_validator(mode="after")
    def validate_config_consistency(self) -> "MyPlatformConfig":
        # Validate relationships between fields
        if self.enable_lineage and self.timeout < 30:
            logger.warning("Lineage extraction may timeout with timeout < 30")
        return self

# Usage
config_dict = {
    "api_url": "https://api.myplatform.com/v2",
    "api_key": "secret_key_123",
    "enable_lineage": True
}

# Parse using v2 method
config = MyPlatformConfig.model_validate(config_dict)

# Serialize using v2 methods
config_dict = config.model_dump()
config_json = config.model_dump_json()
```

##### 6. Essential Imports

```python
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing import Any, Dict, Optional
from typing_extensions import Self  # For type hints in model_validator
```

##### 7. Common Patterns

**Using DataHub's ConfigModel base class**:

```python
from datahub.configuration.common import ConfigModel

class MyConfig(ConfigModel):
    # ConfigModel already has proper ConfigDict setup
    api_url: str
    timeout: int = 30
```

**Permissive config (allows extra fields)**:

```python
from datahub.configuration.common import PermissiveConfigModel

class MyConfig(PermissiveConfigModel):
    # extra="allow" is set automatically
    known_field: str
    # Unknown fields will be allowed
```

**Arbitrary types (for complex objects)**:

```python
from datahub.ingestion.graph.client import DataHubGraph

class MyConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Can now use non-Pydantic types
    graph_client: Optional[DataHubGraph] = None
```

##### 8. Quick Reference

**Don't use these (deprecated)**:

- ❌ `Model.parse_obj()`
- ❌ `model.dict()`
- ❌ `model.json()`
- ❌ `@validator`
- ❌ `@root_validator`
- ❌ `class Config:`

**Use these instead**:

- ✅ `Model.model_validate()`
- ✅ `model.model_dump()`
- ✅ `model.model_dump_json()`
- ✅ `@field_validator(..., mode='after')`
- ✅ `@model_validator(mode='before')` or `mode='after'`
- ✅ `model_config = ConfigDict(...)`

### 3. Documentation

**Location**: `docs/sources/<platform_name>/<platform>_recipe.yml`

Create recipe file with **commented explanations** for all config values:

```yaml
# Example recipe for MyPlatform
# This recipe demonstrates all available configuration options with explanations

source:
  type: myplatform
  config:
    # ============================================
    # Connection Configuration
    # ============================================
    connection:
      # API endpoint URL - required for all capabilities
      api_url: https://api.myplatform.com

      # API authentication key - required for all capabilities
      # Use environment variables for security: ${MYPLATFORM_API_KEY}
      api_key: "${MYPLATFORM_API_KEY}"

      # Optional: Request timeout in seconds (default: 30)
      timeout_seconds: 30

      # Optional: Maximum retry attempts (default: 3)
      max_retries: 3

    # ============================================
    # Filtering Configuration
    # ============================================
    # Filter dashboards by name pattern
    # Required permission: read:dashboards
    dashboard_pattern:
      allow:
        - "^prod_.*" # Allow dashboards starting with "prod_"
      deny:
        - ".*_test$" # Deny dashboards ending with "_test"

    # Filter charts by name pattern
    # Required permission: read:dashboards (to access charts)
    chart_pattern:
      allow:
        - ".*" # Allow all charts by default

    # ============================================
    # Feature Flags
    # ============================================
    # Extract ownership information
    # Required permission: read:users or read:ownership
    extract_ownership: true

    # Extract usage statistics
    # Required permission: read:usage (additional permission beyond basic read)
    extract_usage_stats: false

    # Extract lineage information
    # Required permission: read:dashboards, read:datasets (for lineage resolution)
    extract_lineage: true

    # ============================================
    # Stateful Ingestion
    # ============================================
    # Enable stateful ingestion for deletion detection
    # Required permission: read:dashboards (to track what exists)
    stateful_ingestion:
      enabled: true
      remove_stale_metadata: true # Remove entities that no longer exist

    # ============================================
    # Platform Instance (Optional)
    # ============================================
    # Platform instance identifier for multi-tenant deployments
    # platform_instance: "production"

    # ============================================
    # Environment (Optional)
    # ============================================
    # Environment tag (PROD, DEV, etc.)
    # env: "PROD"

sink:
  type: datahub-rest
  config:
    server: http://localhost:8080
```

**Key Requirements for Recipe Files:**

1. **Comment All Config Values**: Every configuration option should have a comment explaining:
   - What it does
   - When it's required vs optional
   - Default values
   - Any dependencies or prerequisites

2. **Group Related Options**: Use comment sections to group related configuration options

3. **Document Permissions**: For each feature/capability, note the required permissions in comments

4. **Show Environment Variables**: Demonstrate using environment variables for sensitive values

5. **Include Optional Fields**: Show optional fields with comments explaining when they're useful

### 4. README

**Location**: `docs/sources/<platform_name>/<platform>.md`

Create the main documentation file with **permissions documentation per capability**:

````markdown
# MyPlatform Source

## Overview

Ingests metadata from MyPlatform including dashboards, charts, and lineage.

## Capabilities

- Dashboard & Chart Metadata
- Ownership
- Lineage to datasets
- Usage Statistics (optional)
- Stale entity removal

## Prerequisites

- MyPlatform API access
- Python 3.8 or newer
- Required Python packages (if any)

## Required Permissions

### Minimum Required Permissions (Basic Metadata Extraction)

To extract basic metadata (dashboards, charts), you need:

- **`read:dashboards`** - Read access to dashboards
- **`read:workspaces`** - Read access to workspaces (for container hierarchy)

### Permissions by Capability

#### Schema Metadata (`SCHEMA_METADATA`)

- **Required**: `read:dashboards`, `read:charts`
- **Description**: Access to dashboard and chart metadata

#### Descriptions (`DESCRIPTIONS`)

- **Required**: `read:dashboards`, `read:charts`
- **Description**: Access to dashboard and chart descriptions

#### Ownership (`OWNERSHIP`)

- **Required**: `read:users` OR `read:ownership`
- **Description**: Access to user/owner information for dashboards and charts
- **Note**: If `extract_ownership: false`, this permission is not required

#### Lineage (`LINEAGE_COARSE`, `LINEAGE_FINE`)

- **Required**: `read:dashboards`, `read:datasets`
- **Description**:
  - `read:dashboards` - To access dashboard lineage information
  - `read:datasets` - To resolve dataset references in lineage
- **Note**: Lineage extraction requires access to both source and target datasets

#### Usage Statistics (`USAGE_STATS`)

- **Required**: `read:usage` (additional permission)
- **Description**: Access to usage/query statistics
- **Note**: This is an additional permission beyond basic read access. If `extract_usage_stats: false`, this permission is not required

#### Platform Instance (`PLATFORM_INSTANCE`)

- **Required**: No additional permissions
- **Description**: Platform instance is a metadata tag, no special permissions needed

#### Domains (`DOMAINS`)

- **Required**: No additional permissions
- **Description**: Domain assignment is a metadata tag, no special permissions needed

#### Deletion Detection (`DELETION_DETECTION`)

- **Required**: `read:dashboards` (to track what exists)
- **Description**: Requires ability to list all dashboards to detect deletions

#### Test Connection (`TEST_CONNECTION`)

- **Required**: `read:dashboards` (minimal - just to verify access)
- **Description**: Basic connectivity and permission verification

### Permission Testing

Test your API key permissions:

```bash
# Test basic connectivity
curl -H "Authorization: Bearer YOUR_KEY" https://api.myplatform.com/ping

# Test permissions
curl -H "Authorization: Bearer YOUR_KEY" https://api.myplatform.com/permissions
```

## Configuration

See [myplatform_recipe.yml](myplatform_recipe.yml) for a complete example with all options commented.

### Connection Options

| Option            | Type   | Required | Default | Description            | Required Permission |
| ----------------- | ------ | -------- | ------- | ---------------------- | ------------------- |
| `api_url`         | string | ✅       |         | API base URL           | N/A                 |
| `api_key`         | string | ✅       |         | API authentication key | N/A                 |
| `timeout_seconds` | int    |          | 30      | Request timeout        | N/A                 |

### Feature Options

| Option                | Type | Default | Description              | Required Permission |
| --------------------- | ---- | ------- | ------------------------ | ------------------- |
| `extract_ownership`   | bool | true    | Extract ownership info   | `read:users`        |
| `extract_usage_stats` | bool | false   | Extract usage statistics | `read:usage`        |
| `extract_lineage`     | bool | true    | Extract lineage          | `read:datasets`     |

## Troubleshooting

### Permission Errors

If you see permission errors, verify your API key has the required permissions:

```bash
curl -H "Authorization: Bearer YOUR_KEY" https://api.myplatform.com/permissions
```

Common issues:

- **403 Forbidden**: Missing required permission (check capability requirements above)
- **401 Unauthorized**: Invalid API key
- **404 Not Found**: API endpoint incorrect or resource doesn't exist

### Rate Limiting

The source implements automatic retry with exponential backoff. For aggressive rate limits, increase `timeout_seconds`.
````

**Key Requirements for README Files:**

1. **Permissions Section**: Always include a "Required Permissions" section that lists:
   - Minimum required permissions for basic functionality
   - Permissions organized by capability (matching the `@capability` decorators)
   - Clear indication of which permissions are needed for optional features

2. **Permission Testing**: Include commands/examples for testing permissions

3. **Configuration Table**: Include a "Required Permission" column in configuration tables

4. **Troubleshooting**: Include permission-related troubleshooting guidance

### Rate Limiting

The source implements automatic retry with exponential backoff. For aggressive rate limits, increase `timeout_seconds`.

```

```
