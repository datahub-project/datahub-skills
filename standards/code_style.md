# Code Style Guidelines

This guide covers general Python code quality standards for DataHub connectors. These rules apply to all connector code regardless of source type.

## Related Guides

- [Main Guide](main.md) - Overview and quick start
- [Common Patterns](patterns.md) - Connector-specific patterns and file organization
- [Testing Guide](testing.md) - Testing approaches and frameworks
- [SQL Sources](sql.md) - For SQL database sources
- [API-Based Sources](api.md) - For REST/GraphQL API sources

---

## Table of Contents

1. [Formatting](#formatting)
2. [Naming Conventions](#naming-conventions)
3. [Data Structures](#data-structures)
4. [Architecture Guidelines](#architecture-guidelines)
5. [Code Quality Rules](#code-quality-rules)
6. [Type Safety and Mypy Compliance](#type-safety-and-mypy-compliance)
7. [Quick Code Style Checklist](#quick-code-style-checklist)

---

## Formatting

**Tool**: Use `ruff format` for all code formatting.

```bash
# Format all connector code
ruff format src/datahub/ingestion/source/<connector_name>/

# Check formatting without modifying
ruff format --check src/datahub/ingestion/source/<connector_name>/
```

**Pre-commit check**: Always run `ruff format` before committing code.

---

## Naming Conventions

### Match Source System Terminology

Use names that match the source system's documentation and API.

```python
# ✅ GOOD - Matches BigQuery terminology
class BigQueryConfig:
    project_id: str       # BigQuery calls it "project"
    dataset_id: str       # BigQuery calls it "dataset"

# ❌ BAD - Using generic terms
class BigQueryConfig:
    database_name: str    # BigQuery doesn't use "database"
    schema_name: str      # BigQuery doesn't use "schema"
```

### Descriptive Names

Use clear, descriptive names that explain purpose.

```python
# ✅ GOOD - Clear purpose
def extract_table_lineage(self, table: TableInfo) -> List[UpstreamLineage]:
    ...

# ❌ BAD - Unclear purpose
def process(self, t) -> List[Any]:
    ...
```

---

## Data Structures

**Use dataclasses or Pydantic models** for structured data, not tuples or dicts.

```python
# ✅ GOOD - Structured dataclass
from dataclasses import dataclass

@dataclass
class TableInfo:
    name: str
    schema: str
    columns: List[ColumnInfo]
    description: Optional[str] = None

def get_table_info(self, table_id: str) -> TableInfo:
    return TableInfo(
        name="my_table",
        schema="public",
        columns=[...],
    )

# ❌ BAD - Unstructured tuple
def get_table_info(self, table_id: str) -> Tuple[str, str, List[Any], Optional[str]]:
    return ("my_table", "public", [...], None)  # What is each field?

# ❌ BAD - Unstructured dict
def get_table_info(self, table_id: str) -> Dict[str, Any]:
    return {"name": "my_table", "schema": "public", ...}  # No type safety
```

**Why dataclasses?**

- Type safety and IDE autocomplete
- Self-documenting code
- Easy to extend with methods
- Default values and validation

---

## Architecture Guidelines

**Avoid tall inheritance hierarchies**: Prefer composition over deep inheritance. Keep inheritance to 2-3 levels maximum.

```python
# ✅ GOOD - Flat with mixins
class MySource(
    StatefulIngestionSourceBase,
    TestableSource,                    # Mixin for test_connection
    LineageParserInterface,            # Mixin for lineage parsing
):
    pass

# ❌ BAD - Deep inheritance
class MySource(BaseSource):
    pass

class BaseSource(AbstractSource):
    pass

class AbstractSource(GenericSource):
    pass

class GenericSource(Source):  # 4+ levels deep
    pass
```

**Why avoid deep hierarchies?**

- Hard to understand behavior
- Changes in base classes ripple unexpectedly
- Difficult to test in isolation
- Makes debugging harder

---

## Code Quality Rules

### Avoid Global State

Don't use module-level mutable variables.

```python
# ❌ BAD - Global mutable state
_cached_connection = None

def get_connection():
    global _cached_connection
    if _cached_connection is None:
        _cached_connection = create_connection()
    return _cached_connection

# ✅ GOOD - Instance-level state
class MySource:
    def __init__(self):
        self._connection: Optional[Connection] = None

    def get_connection(self) -> Connection:
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection
```

### Use Named Arguments

For functions with more than 2-3 parameters.

```python
# ✅ GOOD - Named arguments
dataset = create_dataset(
    platform="bigquery",
    name="project.dataset.table",
    env="PROD",
    description="Sales data",
)

# ❌ BAD - Positional arguments (hard to read)
dataset = create_dataset("bigquery", "project.dataset.table", "PROD", "Sales data")
```

### Don't Re-export in `__init__.py`

Unless necessary for public API.

```python
# ✅ GOOD - Empty __init__.py (most cases)
# __init__.py is empty

# ✅ GOOD - Only export main source class if needed
# __init__.py
from datahub.ingestion.source.myplatform.myplatform import MyPlatformSource

# ❌ BAD - Re-exporting everything
# __init__.py
from .myplatform import *
from .myplatform_config import *
from .myplatform_client import *
```

---

## Type Safety and Mypy Compliance

### 🔴 BLOCKER: All Code Must Pass Mypy

**All connector code MUST pass mypy type checking without errors.** Type safety is critical for maintainability and catching bugs early.

### Type Hints Are Required

**All public methods and functions MUST have type hints:**

```python
# ✅ CORRECT - Fully typed
def get_tables(self, schema_name: str) -> List[TableInfo]:
    ...

def process_entity(
    self,
    entity: Dict[str, Any],
    include_metadata: bool = True,
) -> Optional[MetadataWorkUnit]:
    ...

# ❌ WRONG - Missing type hints
def get_tables(self, schema_name):
    ...
```

### 🔴 BLOCKER: Avoid `Any` Type Unless Justified

**Do NOT use `Any` as a lazy escape hatch.** Only use `Any` when:

1. **External API returns truly dynamic data** (and document why)
2. **Interfacing with untyped third-party libraries** (and document why)
3. **Generic containers that genuinely accept anything** (rare)

```python
# ✅ CORRECT - Specific types
def process_table(self, table: TableMetadata) -> DatasetProperties:
    ...

def get_columns(self, table_id: str) -> List[ColumnInfo]:
    ...

# ✅ ACCEPTABLE - Any with justification
def parse_api_response(self, response: Dict[str, Any]) -> TableMetadata:
    """Parse API response. Uses Any because API schema is not strictly typed."""
    ...

# ❌ WRONG - Lazy use of Any
def process_data(self, data: Any) -> Any:  # What types are these?
    ...
```

### 🔴 BLOCKER: Use `isinstance()` Instead of `cast()`

**Do NOT use `cast()` to silence type errors.** Use `isinstance()` for runtime type narrowing:

```python
from typing import Union

# ✅ CORRECT - isinstance() for type narrowing
def process_value(self, value: Union[str, int, dict]) -> str:
    if isinstance(value, str):
        return value
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, dict):
        return json.dumps(value)
    else:
        raise TypeError(f"Unexpected type: {type(value)}")

# ✅ CORRECT - isinstance() with multiple types
def handle_owner(self, owner: Union[str, Dict[str, str], OwnerInfo]) -> str:
    if isinstance(owner, str):
        return owner
    elif isinstance(owner, dict):
        return owner.get("email", owner.get("id", "unknown"))
    elif isinstance(owner, OwnerInfo):
        return owner.email
    raise TypeError(f"Unexpected owner type: {type(owner)}")

# ❌ WRONG - cast() hides bugs
from typing import cast

def process_value(self, value: Union[str, int]) -> str:
    return cast(str, value)  # WRONG: Will fail at runtime if int!

# ❌ WRONG - cast() to silence mypy
def get_table(self, response: Dict[str, Any]) -> TableInfo:
    return cast(TableInfo, response["table"])  # WRONG: No runtime check!
```

### 🔴 BLOCKER: Only Silence Mypy Errors If Justified

**Do NOT add `# type: ignore` without justification.** When you must silence mypy:

1. **Always include a reason**
2. **Use the most specific ignore code**
3. **Document why the error is incorrect or unavoidable**

```python
# ✅ CORRECT - Specific ignore with justification
result = untyped_library.get_data()  # type: ignore[no-untyped-call]  # Third-party lib lacks stubs

# ✅ CORRECT - Documented unavoidable ignore
# SQLAlchemy's inspect() returns different types based on input, mypy can't track this
inspector = inspect(engine)  # type: ignore[arg-type]

# ❌ WRONG - Blanket ignore without reason
result = some_function()  # type: ignore

# ❌ WRONG - Ignoring to avoid fixing actual bug
def bad_function(self, x) -> str:  # type: ignore  # WRONG: Just add type hints!
    return x
```

### Type Narrowing Patterns

**Common patterns for safe type narrowing:**

```python
from typing import Optional, Union, TypeGuard

# Pattern 1: Optional handling
def process_optional(self, value: Optional[str]) -> str:
    if value is None:
        return "default"
    return value  # mypy knows this is str

# Pattern 2: Union discrimination
def process_union(self, item: Union[Table, View]) -> str:
    if isinstance(item, Table):
        return f"table:{item.name}"
    else:
        return f"view:{item.name}"

# Pattern 3: TypeGuard for complex checks
def is_valid_table(item: Dict[str, Any]) -> TypeGuard[TableDict]:
    return (
        isinstance(item, dict)
        and "name" in item
        and "columns" in item
        and isinstance(item["columns"], list)
    )

def process_items(self, items: List[Dict[str, Any]]) -> List[str]:
    return [
        item["name"]
        for item in items
        if is_valid_table(item)  # mypy narrows type here
    ]
```

---

## Quick Code Style Checklist

| Rule                          | Required       | Check                                            |
| ----------------------------- | -------------- | ------------------------------------------------ |
| `ruff format` passes          | 🔴 BLOCKER     | `ruff format --check .`                          |
| `mypy` passes                 | 🔴 BLOCKER     | `mypy src/datahub/ingestion/source/myconnector/` |
| Names match source system     | 🟡 Recommended | Manual review                                    |
| Use dataclasses for data      | 🟡 Recommended | No tuple/dict returns                            |
| Flat inheritance              | 🟡 Recommended | Max 2-3 levels                                   |
| No global state               | 🔴 BLOCKER     | No module-level mutables                         |
| Named arguments for 3+ params | 🟡 Recommended | Manual review                                    |

### Type Safety Rules

| Rule                                | Required   | Example                                                                                           |
| ----------------------------------- | ---------- | ------------------------------------------------------------------------------------------------- |
| Type hints on public methods        | 🔴 BLOCKER | `def get_tables(self) -> List[Table]:`                                                            |
| Avoid `Any` without justification   | 🔴 BLOCKER | Use specific types or document why `Any` is needed                                                |
| Use `isinstance()` not `cast()`     | 🔴 BLOCKER | `if isinstance(x, str): ...`                                                                      |
| Mypy ignores need justification     | 🔴 BLOCKER | `# type: ignore[specific-code]  # reason`                                                         |
| Pass mypy with no errors            | 🔴 BLOCKER | `mypy src/datahub/ingestion/source/myconnector/`                                                  |
| `LiteralString` for report messages | 🔴 BLOCKER | See [Error Reporting Guide](patterns.md#-blocker-literalstring-requirement-for-title-and-message) |

### 🔴 BLOCKER: LiteralString in Error Reporting

When using `self.report.warning()`, `self.report.failure()`, or similar methods, the `title` and `message` parameters are typed as `LiteralString`. This means they **MUST be constant strings** - no f-strings with variables, no string concatenation.

```python
# ✅ CORRECT - Constants for title/message, dynamic value in context
self.report.warning(
    title="Failed to extract lineage",
    message="View definition could not be parsed.",
    context=f"{schema}.{view_name}",  # Dynamic values go in context
    exc=e,
)

# ❌ WRONG - f-string in message (violates LiteralString)
self.report.warning(
    f"{db_name}.{schema}",  # WRONG!
    "Some message",
)

# ❌ WRONG - Variable in title
self.report.warning(
    title=f"Error in {table_name}",  # WRONG!
    message="Processing failed",
)
```

**Why?** `title + message` are used as aggregation keys for error grouping. Dynamic values would create unbounded unique keys. See [patterns.md](patterns.md#warning-and-error-reporting-style-guide) for complete guidelines.
