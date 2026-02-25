# Testing Guide for DataHub Sources

**🚨 TOTAL AND ABSOLUTE BLOCKER**: Trivial tests are an IMMEDIATE REJECTION trigger. No exceptions. No appeals. No "but it's just one test".

**🔴 ABSOLUTE BLOCKER**: Testing is THE primary indicator of code quality. Tests must verify BUSINESS LOGIC, not configuration defaults or trivial getters.

**Code containing trivial tests or anti-pattern tests WILL BE REJECTED WITHOUT FURTHER REVIEW. This is non-negotiable.**

The presence of even ONE trivial test (testing defaults, testing getters, testing `platform == "platform"`) indicates fundamental misunderstanding of testing principles and results in automatic PR rejection.

## Related Guides

- [Main Guide](main.md) - Overview and quick start
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [SQL Sources](sql.md) - For SQL database sources
- [API-Based Sources](api.md) - For REST/GraphQL API sources
- [Common Patterns](patterns.md) - Shared patterns and utilities
- [Lineage Extraction](lineage.md) - Implementing lineage
- [Performance](performance.md) - Performance and memory optimization
- [Registration & Documentation](registration.md) - Final steps

---

## Test File Organization and Conventions

### Test Directory Structure

**Tests go in `tests/` directory alongside `src/`, NOT inside `src/`.**

```
metadata-ingestion/
├── src/
│   └── datahub/
│       └── ingestion/
│           └── source/
│               └── myplatform/
│                   ├── myplatform.py
│                   └── myplatform_config.py
└── tests/
    ├── unit/
    │   └── myplatform/
    │       └── test_myplatform.py       # Unit tests
    └── integration/
        └── myplatform/
            ├── test_myplatform.py        # Integration tests
            ├── docker-compose.yml        # Test infrastructure
            └── myplatform_mces_golden.json  # Golden file
```

**Test directory structure should mirror source directory structure** for easy navigation.

### Testing Framework: pytest (NOT unittest)

**Use pytest, NOT unittest.** DataHub uses pytest for all tests.

```python
# ✅ GOOD - pytest style
import pytest

class TestMyPlatformSource:
    def test_extracts_tables(self, mock_client):
        source = MyPlatformSource(config, ctx)
        tables = list(source.get_tables())
        assert len(tables) == 5

    def test_handles_empty_schema(self):
        with pytest.raises(ValueError):
            MyPlatformConfig(schema="")

# ❌ BAD - unittest style (DO NOT USE)
import unittest

class TestMyPlatformSource(unittest.TestCase):  # ❌ Don't use TestCase
    def test_extracts_tables(self):
        source = MyPlatformSource(config, ctx)
        tables = list(source.get_tables())
        self.assertEqual(len(tables), 5)  # ❌ Don't use self.assertEqual
```

### Assertions: Use `assert` Statements

**Use plain `assert` statements, NOT `self.assertEqual()` or similar.**

```python
# ✅ GOOD - assert statements
assert result == expected
assert len(items) == 5
assert "error" in message.lower()
assert table.name == "users"

# ❌ BAD - unittest assertions
self.assertEqual(result, expected)
self.assertTrue(len(items) == 5)
self.assertIn("error", message.lower())
```

### Test Naming Convention

**Test files MUST be named `test_*.py`** (pytest discovery pattern).

```
# ✅ GOOD - pytest can discover these
test_myplatform.py
test_myplatform_config.py
test_myplatform_lineage.py

# ❌ BAD - pytest won't discover these
myplatform_test.py
myplatform_tests.py
tests_myplatform.py
```

**Test functions/methods MUST start with `test_`:**

```python
# ✅ GOOD
def test_extracts_tables():
    ...

def test_handles_connection_error():
    ...

# ❌ BAD
def extracts_tables_test():  # Wrong suffix
    ...

def check_extracts_tables():  # Missing test_ prefix
    ...
```

### Test Class Convention

**Use regular classes, NOT `unittest.TestCase`:**

```python
# ✅ GOOD - Regular class
class TestMyPlatformSource:
    """Tests for MyPlatformSource."""

    def test_extracts_tables(self):
        ...

    def test_handles_errors(self):
        ...

# ✅ GOOD - No class at all (module-level functions)
def test_extracts_tables():
    ...

def test_handles_errors():
    ...

# ❌ BAD - unittest.TestCase
class TestMyPlatformSource(unittest.TestCase):  # ❌ Don't inherit TestCase
    def test_extracts_tables(self):
        ...
```

### Quick Conventions Checklist

| Convention                  | Required   | Check                   |
| --------------------------- | ---------- | ----------------------- |
| Tests in `tests/` directory | 🔴 BLOCKER | NOT in `src/`           |
| Use pytest                  | 🔴 BLOCKER | No unittest imports     |
| Use `assert` statements     | 🔴 BLOCKER | No `self.assertEqual()` |
| Files named `test_*.py`     | 🔴 BLOCKER | pytest discovery        |
| Functions named `test_*`    | 🔴 BLOCKER | pytest discovery        |
| No `unittest.TestCase`      | 🔴 BLOCKER | Regular classes         |

---

## 🔴 MANDATORY: Use time-machine, NOT freezegun

**DataHub uses `time-machine` for time mocking, NOT `freezegun`.**

**❌ DO NOT USE freezegun**:

```python
# ❌ WRONG - Do not use freezegun
from freezegun import freeze_time

@freeze_time("2020-04-14 07:00:00")
def test_something():
    ...
```

**✅ USE time-machine**:

```python
# ✅ CORRECT - Use time-machine
import time_machine

@time_machine.travel("2020-04-14 07:00:00")
def test_something():
    ...
```

**Why time-machine over freezegun**:

- Better performance (C extension)
- More reliable with async code
- Better compatibility with modern Python
- DataHub standard - all existing tests use it

**Import pattern**:

```python
import time_machine

FROZEN_TIME = "2022-03-06 14:00:00"

@time_machine.travel(FROZEN_TIME)
@pytest.mark.integration
def test_my_integration(runner, pytestconfig, tmp_path, mock_time):
    ...
```

---

## Testing Philosophy

### ⚠️ CRITICAL: What Makes a Good Test

**Good tests verify BUSINESS LOGIC and BEHAVIOR:**

- ✅ Data transformation and mapping logic
- ✅ Error handling and recovery
- ✅ Filtering and pattern matching behavior
- ✅ API response parsing and edge cases
- ✅ Lineage extraction logic (see "Testing Lineage" section below)
- ✅ Type conversion and custom type handling
- ✅ Complex configuration interactions

**Bad tests verify TRIVIAL or OBVIOUS behavior:**

- ❌ Testing default configuration values
- ❌ Testing simple getters/setters
- ❌ Testing that a class can be instantiated
- ❌ Testing framework behavior (SQLAlchemy, pydantic)
- ❌ Testing type registration without verification
- ❌ Testing obvious equality (platform == "platform")

---

## 🔴 ABSOLUTE BLOCKERS: Tests That Must NOT Be Written

**ANY code containing these test anti-patterns will be REJECTED immediately. No exceptions.**

These tests provide zero value, waste maintenance effort, and indicate a fundamental misunderstanding of testing principles.

### 0. Late/Inline Imports (ABSOLUTE BLOCKER)

**Late imports (imports inside functions, methods, or test bodies) are an ABSOLUTE BLOCKER.**

**❌ BAD - Imports Hidden Inside Functions**:

```python
def test_session_handle_extracted(self, mock_session_class):
    from datahub.ingestion.source.flink.flink_sql_gateway_client import (
        FlinkSQLGatewayClient,  # ❌ Import inside function
    )
    from datahub.ingestion.api.common import PipelineContext  # ❌ Import inside function

    # ... test code
```

**Why This Is An Absolute Blocker**:

- Hides dependencies - makes it hard to see what a test file depends on
- Breaks IDE navigation and refactoring tools
- Inconsistent with Python best practices (PEP 8)
- Makes tests harder to maintain and review
- Can mask import errors until runtime
- Creates inconsistent code style across test files
- Makes it harder to identify circular import issues early

**✅ GOOD - All Imports at Top of File**:

```python
# All imports at the top of the test file
from unittest.mock import MagicMock, patch

import pytest

from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.source.flink.flink_config import FlinkSourceConfig
from datahub.ingestion.source.flink.flink_source import FlinkSource
from datahub.ingestion.source.flink.flink_sql_gateway_client import FlinkSQLGatewayClient


class TestFlinkSQLGatewayClient:
    def test_session_handle_extracted(self, mock_session_class):
        # Test code uses imports from top of file
        client = FlinkSQLGatewayClient(config)
        # ...
```

**Rule**: ALL imports MUST be at the top of the test file, following standard Python conventions (stdlib → third-party → local).

#### Rare Exceptions (Must Be Documented)

In extremely rare cases, late imports may be acceptable IF:

1. There is a **documented technical reason** (e.g., avoiding circular imports that cannot be resolved otherwise)
2. The import has a **comment explaining WHY** it must be late
3. The exception is **called out during code review**

```python
def test_something_with_circular_dependency():
    # LATE IMPORT: Required to avoid circular import with module X
    # See issue #1234 for details on why this cannot be resolved at module level
    from datahub.some.module import SomeClass
```

**If you see a late import without such documentation during review, it is an AUTOMATIC REJECTION.**

---

### 1. Testing Default Configuration Values (ABSOLUTE BLOCKER)

**❌ BAD - Useless Test**:

```python
def test_doris_stored_procedures_disabled_by_default():
    """Test that stored procedures are disabled by default for Doris"""
    config = DorisConfig()
    assert config.include_stored_procedures is False  # ❌ Just tests pydantic default
```

**Why This Is Bad**:

- Tests pydantic Field default behavior, not YOUR code
- Provides zero confidence in business logic
- Becomes maintenance burden when defaults change
- Gives false sense of test coverage

**✅ GOOD - Test Business Logic Instead**:

```python
def test_stored_procedures_ignored_even_when_enabled():
    """Test that Doris source returns empty list even when user tries to enable stored procedures"""
    config = DorisConfig(include_stored_procedures=True)
    inspector = Mock()
    inspector.get_stored_procedure_names.return_value = ["proc1", "proc2"]

    source = DorisSource(config, ctx)
    procedures = source.get_procedures_for_schema(inspector, "testdb", "testschema")

    # Verify business rule: Doris ALWAYS returns empty, regardless of config
    assert procedures == []
    # Verify warning was issued
    assert "not supported in Apache Doris" in source.report.warnings[0].message
```

---

### 2. Testing Trivial Getters (ABSOLUTE BLOCKER)

**❌ BAD - Useless Test - WILL BE REJECTED**:

```python
def test_platform_correctly_set_doris():
    source = DorisSource(ctx=PipelineContext(run_id="test"), config=DorisConfig())
    assert source.platform == "doris"  # ❌ Just tests get_platform() returns hardcoded string
```

**Why This Is Bad**:

- One-line method returns hardcoded value
- No logic to test
- Cannot possibly fail unless you make a typo
- Clutters test suite

**✅ GOOD - Test Platform Usage in Context**:

```python
def test_dataset_urns_use_correct_platform():
    """Test that generated dataset URNs use doris platform, not mysql"""
    config = DorisConfig(host_port="localhost:9030", database="testdb")
    source = DorisSource(config, ctx)

    # Mock inspector to return test table
    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_table_names.return_value = ["users"]
        mock_inspector.get_columns.return_value = [{"name": "id", "type": "INT"}]

        workunits = list(source.get_workunits())

        # Verify URN uses 'doris' platform, not 'mysql'
        dataset_urn = workunits[0].metadata.proposedSnapshot.urn
        assert "urn:li:dataPlatform:doris" in dataset_urn
        assert "urn:li:dataPlatform:mysql" not in dataset_urn
```

---

### 3. Testing Type Registration Without Verification

**❌ BAD - Incomplete Test**:

```python
def test_doris_custom_types_registered():
    """Test that Doris-specific types are properly registered with SQLAlchemy"""
    assert "hll" in base.ischema_names  # ❌ Tests registration, not actual usage
    assert "bitmap" in base.ischema_names
    assert base.ischema_names["hll"] == HLL
```

**Why This Is Bad**:

- Tests module-level side effect, not business logic
- Doesn't verify types actually WORK when encountered
- Doesn't test case sensitivity handling
- Doesn't test DataHub type mapping

**✅ GOOD - Test Type Handling in Real Scenario**:

```python
def test_doris_custom_types_correctly_converted_in_schema():
    """Test that Doris custom types are correctly converted to DataHub types"""
    config = DorisConfig(host_port="localhost:9030", database="testdb")
    source = DorisSource(config, ctx)

    # Mock inspector to return table with Doris custom types
    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_table_names.return_value = ["analytics"]
        mock_inspector.get_columns.return_value = [
            {"name": "user_hll", "type": HLL()},  # HyperLogLog column
            {"name": "user_bitmap", "type": BITMAP()},  # Bitmap column
            {"name": "tags", "type": DORIS_ARRAY()},  # Array column
            {"name": "metadata", "type": JSONB()},  # JSONB column
        ]

        workunits = list(source.get_workunits())
        schema_metadata = workunits[0].metadata.proposedSnapshot.aspects[0]

        # Verify DataHub types
        fields = {f.fieldPath: f.nativeDataType for f in schema_metadata.fields}
        assert fields["user_hll"] == "HLL"  # Preserved native type
        assert fields["user_bitmap"] == "BITMAP"
        assert fields["tags"] == "ARRAY"
        assert fields["metadata"] == "JSONB"

        # Verify DataHub type classes
        field_types = {f.fieldPath: type(f.type).__name__ for f in schema_metadata.fields}
        assert field_types["user_hll"] == "BytesTypeClass"
        assert field_types["user_bitmap"] == "BytesTypeClass"
        assert field_types["tags"] == "ArrayTypeClass"
        assert field_types["metadata"] == "RecordTypeClass"
```

---

### 4. Testing Framework Behavior

**❌ BAD - Testing Pydantic**:

```python
def test_config_has_correct_fields():
    config = DorisConfig(host_port="localhost:9030")
    assert hasattr(config, "host_port")  # ❌ Tests pydantic, not your code
    assert hasattr(config, "username")
```

**✅ GOOD - Test Configuration Validation Logic**:

```python
def test_invalid_port_rejected():
    """Test that invalid port numbers are rejected"""
    with pytest.raises(ValidationError) as exc:
        DorisConfig(host_port="localhost:invalid")

    assert "port must be numeric" in str(exc.value).lower()

def test_doris_default_port_differs_from_mysql():
    """Test that Doris uses 9030, not MySQL's 3306"""
    doris_config = DorisConfig()
    mysql_config = MySQLConfig()

    assert "9030" in doris_config.host_port
    assert "3306" in mysql_config.host_port
```

---

### 5. Testing Shared/Common Utilities (ABSOLUTE BLOCKER)

**❌ BAD - Testing AllowDenyPattern in Connector Tests**:

```python
class TestMyConnectorPatternFiltering:
    """DO NOT write these tests in connector code"""

    def test_catalog_pattern_allows_matching(self):
        config = MyConnectorConfig(catalog_pattern={"allow": ["^prod_.*"]})
        assert config.catalog_pattern.allowed("prod_catalog")  # ❌ Tests AllowDenyPattern, not your connector

    def test_database_pattern_deny_takes_precedence(self):
        config = MyConnectorConfig(database_pattern={"allow": [".*"], "deny": ["^test_.*"]})
        assert not config.database_pattern.allowed("test_db")  # ❌ Tests shared utility
```

**Why This Is Bad**:

- `AllowDenyPattern` is a **shared utility class** used by ALL connectors
- It has its own test suite in `tests/unit/test_allow_deny.py`
- You are testing DataHub framework code, not your connector logic
- If AllowDenyPattern breaks, the shared tests will catch it - not your connector tests

**What TO Test Instead**:
Test how your connector **uses** patterns in its specific business logic:

```python
def test_internal_catalogs_excluded_by_default(self):
    """Test that Flink's internal catalogs are excluded even without explicit pattern"""
    config = FlinkSourceConfig(connection={"sql_gateway_url": "http://localhost:8083"})
    source = FlinkSource(config, ctx)

    # Mock SQL Gateway to return internal + user catalogs
    with patch.object(source.client, 'list_catalogs') as mock:
        mock.return_value = ["default_catalog", "my_catalog", "__internal__"]

        catalogs = list(source._get_filtered_catalogs())

        # Verify internal catalogs are excluded by connector logic
        assert "my_catalog" in catalogs
        assert "__internal__" not in catalogs  # Connector-specific exclusion
```

**Rule**: If a class/function is used by multiple connectors, it's a shared utility and should NOT be tested in your connector's test file.

---

## ✅ GOOD TEST PATTERNS

### Unit Tests - Business Logic Focus

**Location**: `tests/unit/test_<platform>.py`

#### Pattern 1: Test Data Transformation Logic

```python
def test_view_definition_sql_extraction():
    """Test that view definitions are correctly extracted and SQL is parsed"""
    config = DorisConfig(
        host_port="localhost:9030",
        database="testdb",
        include_view_lineage=True
    )
    source = DorisSource(config, ctx)

    # Mock view with upstream table references
    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_view_names.return_value = ["user_summary"]
        mock_inspector.get_view_definition.return_value = """
            SELECT u.id, u.name, o.total_orders
            FROM users u
            JOIN orders o ON u.id = o.user_id
        """

        workunits = list(source.get_workunits())

        # Find lineage workunit
        lineage_wu = [wu for wu in workunits if "UpstreamLineage" in str(wu)][0]
        upstreams = lineage_wu.metadata.aspect.upstreams

        # Verify lineage was extracted
        assert len(upstreams) == 2
        upstream_tables = {u.dataset for u in upstreams}
        assert "urn:li:dataset:(urn:li:dataPlatform:doris,testdb.users,PROD)" in upstream_tables
        assert "urn:li:dataset:(urn:li:dataPlatform:doris,testdb.orders,PROD)" in upstream_tables
```

#### Pattern 2: Test Error Handling and Recovery

```python
def test_column_fetch_failure_continues_ingestion():
    """Test that failure to fetch columns for one table doesn't stop ingestion"""
    config = DorisConfig(host_port="localhost:9030", database="testdb")
    source = DorisSource(config, ctx)

    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_table_names.return_value = ["table1", "table2", "table3"]

        # table2 throws error when getting columns
        def get_columns_side_effect(table_name, schema):
            if table_name == "table2":
                raise ProgrammingError("Access denied to table2")
            return [{"name": "id", "type": "INT"}]

        mock_inspector.get_columns.side_effect = get_columns_side_effect

        workunits = list(source.get_workunits())

        # Should have workunits for table1 and table3, not table2
        table_names = {wu.metadata.entityUrn.split(",")[1] for wu in workunits}
        assert "testdb.table1" in table_names
        assert "testdb.table3" in table_names
        assert "testdb.table2" not in table_names

        # Should have warning for table2
        warnings = [w.message for w in source.report.warnings]
        assert any("table2" in w for w in warnings)
```

#### Pattern 3: Test Filtering Logic

```python
def test_table_pattern_filtering_respects_config():
    """Test that table patterns correctly filter tables"""
    config = DorisConfig(
        host_port="localhost:9030",
        database="testdb",
        table_pattern=AllowDenyPattern(
            allow=["^prod_.*"],
            deny=[".*_test$"]
        )
    )
    source = DorisSource(config, ctx)

    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_table_names.return_value = [
            "prod_users",      # Should be included
            "prod_orders",     # Should be included
            "dev_users",       # Should be filtered (not in allow)
            "prod_users_test", # Should be filtered (matches deny)
        ]
        mock_inspector.get_columns.return_value = [{"name": "id", "type": "INT"}]

        workunits = list(source.get_workunits())

        table_names = {wu.metadata.entityUrn.split(",")[1].split(".")[1]
                      for wu in workunits if "dataset" in wu.metadata.entityUrn}

        assert "prod_users" in table_names
        assert "prod_orders" in table_names
        assert "dev_users" not in table_names
        assert "prod_users_test" not in table_names

        # Verify report tracks filtered tables
        assert source.report.filtered.num_tables == 2
```

#### Pattern 4: Test Complex Configuration Interactions

```python
def test_profiling_disabled_when_no_select_permission():
    """Test that profiling gracefully fails when user lacks SELECT permission"""
    config = DorisConfig(
        host_port="localhost:9030",
        database="testdb",
        profiling=ProfilingConfig(enabled=True)
    )
    source = DorisSource(config, ctx)

    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_table_names.return_value = ["secure_table"]
        mock_inspector.get_columns.return_value = [{"name": "id", "type": "INT"}]

        # Mock profiling query to fail with permission error
        with patch.object(source, '_get_profile') as mock_profile:
            mock_profile.side_effect = ProgrammingError("Access denied for SELECT")

            workunits = list(source.get_workunits())

            # Should still emit schema metadata
            assert len(workunits) > 0

            # Should NOT emit profiling aspect
            profiling_wus = [wu for wu in workunits if "DatasetProfile" in str(wu)]
            assert len(profiling_wus) == 0

            # Should have warning about profiling failure
            warnings = [w.message for w in source.report.warnings]
            assert any("profiling" in w.lower() and "permission" in w.lower()
                      for w in warnings)
```

#### Pattern 5: Test Edge Cases and Boundary Conditions

```python
def test_empty_database_returns_no_workunits():
    """Test behavior when database has no tables"""
    config = DorisConfig(host_port="localhost:9030", database="emptydb")
    source = DorisSource(config, ctx)

    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_table_names.return_value = []
        mock_inspector.get_view_names.return_value = []

        workunits = list(source.get_workunits())

        # Should return container workunit for database, but no table workunits
        assert len(workunits) == 1  # Only database container
        assert "container" in workunits[0].metadata.entityUrn.lower()

def test_table_with_no_columns_handled_gracefully():
    """Test handling of malformed table with no columns"""
    config = DorisConfig(host_port="localhost:9030", database="testdb")
    source = DorisSource(config, ctx)

    with patch.object(source, 'inspector') as mock_inspector:
        mock_inspector.get_table_names.return_value = ["empty_table"]
        mock_inspector.get_columns.return_value = []  # No columns

        workunits = list(source.get_workunits())

        # Should handle gracefully (either skip or emit with warning)
        warnings = [w.message for w in source.report.warnings]
        assert any("empty_table" in w and "no columns" in w.lower() for w in warnings)
```

#### Pattern 6: Test Lineage Extraction (MINOR REQUIREMENT for Unit Tests)

**🟡 MINOR REQUIREMENT (Unit Tests)**: Connectors that extract lineage SHOULD have unit tests verifying lineage registration logic.

**🔴 ABSOLUTE BLOCKER (Integration Tests)**: Lineage MUST be comprehensively tested in integration tests with real data and golden file validation. See "Integration Tests" section below.

Even when using `SqlParsingAggregator` (a shared utility), you should still have unit tests that verify your connector:

1. **Correctly registers schemas** with the aggregator
2. **Correctly registers view definitions** with proper context (default_db, default_schema)
3. **Handles lineage extraction errors** gracefully

**✅ GOOD - Test that schemas and views are registered correctly**:

```python
def test_view_definition_registered_with_aggregator():
    """Test that view definitions are correctly registered for lineage extraction."""
    config_dict = {"connection": {"sql_gateway_url": "http://localhost:8083"}}
    ctx = PipelineContext(run_id="test-run")

    with patch("my_source.SqlParsingAggregator") as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        mock_aggregator.gen_metadata.return_value = []

        with patch("my_source.MyAPIClient") as mock_client:
            mock_client.return_value.get_view_definition.return_value = "SELECT * FROM users"
            mock_client.return_value.get_table_schema.return_value = [
                {"name": "id", "type": "INT"},
            ]

            source = MySource.create(config_dict, ctx)
            list(source.get_workunits())

        # Verify view definition was registered with correct context
        mock_aggregator.add_view_definition.assert_called()
        call_args = mock_aggregator.add_view_definition.call_args
        assert call_args.kwargs["view_definition"] == "SELECT * FROM users"
        assert call_args.kwargs["default_db"] == "catalog"
        assert call_args.kwargs["default_schema"] == "schema"

def test_schema_registered_before_view_lineage():
    """Test that table schemas are registered before view lineage is extracted."""
    # This ensures column-level lineage resolution works correctly
    config_dict = {"connection": {"sql_gateway_url": "http://localhost:8083"}}
    ctx = PipelineContext(run_id="test-run")

    with patch("my_source.SqlParsingAggregator") as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator

        # Track call order
        call_order = []
        mock_aggregator.register_schema.side_effect = lambda *a, **kw: call_order.append("schema")
        mock_aggregator.add_view_definition.side_effect = lambda *a, **kw: call_order.append("view")
        mock_aggregator.gen_metadata.return_value = []

        source = MySource.create(config_dict, ctx)
        list(source.get_workunits())

        # Schemas should be registered before view definitions
        schema_indices = [i for i, c in enumerate(call_order) if c == "schema"]
        view_indices = [i for i, c in enumerate(call_order) if c == "view"]
        if schema_indices and view_indices:
            assert max(schema_indices) < min(view_indices), \
                "Schemas must be registered before view definitions for column lineage"

def test_lineage_extraction_error_handled_gracefully():
    """Test that lineage extraction errors don't crash the source."""
    config_dict = {"connection": {"sql_gateway_url": "http://localhost:8083"}}
    ctx = PipelineContext(run_id="test-run")

    with patch("my_source.SqlParsingAggregator") as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator

        # Simulate error during view registration
        mock_aggregator.add_view_definition.side_effect = Exception("SQL parse error")
        mock_aggregator.gen_metadata.return_value = []

        source = MySource.create(config_dict, ctx)
        workunits = list(source.get_workunits())

        # Source should still emit table/view metadata despite lineage error
        assert len(workunits) > 0
        # Warning should be logged
        assert any("lineage" in str(w).lower() for w in source.report.warnings)
```

**Why This Matters**:

- `SqlParsingAggregator` relies on schemas being registered BEFORE view definitions
- Without proper context (default_db, default_schema), table references won't resolve correctly
- Errors in lineage extraction shouldn't crash the entire ingestion

---

## Integration Tests

**🔴 ABSOLUTE BLOCKER**: Integration tests must verify END-TO-END behavior with real database/API.

**Code with incomplete or missing integration tests WILL BE REJECTED. This is non-negotiable.**

### 🔴 ABSOLUTE BLOCKER: Comprehensive Test Data Requirements

**Integration tests are NOT complete until they test ALL major features of the connector with REAL, COMPREHENSIVE test data.**

**Connectors with minimal/incomplete integration tests will be REJECTED immediately.**

#### Common Integration Test Anti-Patterns (ABSOLUTE BLOCKERS)

**❌ BAD - Empty or Minimal Test Data (WILL BE REJECTED)**:

```yaml
# Example with insufficient test data
test_data:
  - tables: [] # Or only 1-2 simple tables
  - No views
  - No lineage
  - Only tests containers/catalogs
```

**Problem**: Integration test passes but only tests container extraction, not actual entity metadata extraction.

**🔴 THIS IS AN ABSOLUTE BLOCKER - Code will be REJECTED if integration tests are this minimal.**

**✅ GOOD - Comprehensive Test Data**:

```yaml
# Example with comprehensive test data
test_data:
  - Multiple databases/schemas
  - tables:
      - users (with various column types)
      - orders (with foreign keys/relationships)
      - products
  - views:
      - user_orders (references users + orders for lineage testing)
      - product_summary (references products for lineage testing)
```

**Result**: Tests verify schema extraction, type mapping, lineage extraction, and container hierarchy.

#### Requirements for Test Environment Setup

When setting up integration test infrastructure (e.g., `docker-compose.yml`), you MUST:

1. **Configure test environment to enable comprehensive testing**:
   - ✅ Test setup must support testing ALL features the connector implements
   - ✅ Test data must be sufficient to validate metadata extraction (tables, views, schemas, lineage)
   - ✅ Test environment must be configured appropriately for the source type (e.g., SQL databases may need volumes, APIs may need fixtures)
   - ✅ Test data must be deterministic (same results on repeated runs)

2. **Create comprehensive test data** covering:
   - ✅ Multiple tables (at least 3-5 for variety)
   - ✅ Various column types (including platform-specific custom types)
   - ✅ Views (if connector supports view lineage)
   - ✅ Foreign keys/relationships (if applicable)
   - ✅ Edge cases (special characters in names, NULL columns, etc.)

3. **Ensure test determinism**:
   - ✅ Running test multiple times produces identical results
   - ✅ Test data is immutable and consistent
   - ✅ Golden file tests produce consistent results

4. **Match production scenarios**:
   - ✅ Use realistic table structures
   - ✅ Use realistic view definitions
   - ✅ Test configurations users will actually use

#### Common Test Setup Approaches

**For SQL Database Sources**:

- Pre-create database file with test schema and data
- Mount database data directory as volume in docker-compose
- Or use database initialization scripts that run on container start

**For API-Based Sources**:

- Use fixture files with captured API responses
- Or use mock server with predefined responses
- Or use test instance/sandbox environment with pre-configured test data

**For File-Based Sources**:

- Include test files in `tests/integration/<platform>/` directory
- Mount test file directory in docker-compose

**Key principle**: Test setup should enable testing all connector features deterministically

#### Recommended Integration Test Development Workflow

The recommended approach for developing integration tests:

**Phase 1: Manual Exploration**

1. **Create docker-compose.yml** with the source system
2. **Start docker-compose manually**: `docker-compose up -d`
3. **Create a test recipe** and ingest into local DataHub
4. **Visually verify in DataHub UI** (http://localhost:9002)
5. **Iterate** until the ingested metadata looks correct

**Phase 2: Automate**

1. **Create setup_test_data.py** that programmatically creates test data:
   - For databases: Create tables, views, insert sample data
   - For APIs: Set up test fixtures or mock responses
   - For systems with session-scoped state: Return session handles for reuse

2. **Create test\_<connector>.py** with:
   - `<connector>_runner` fixture: Starts docker-compose, waits for service
   - `<connector>_test_data` fixture: Runs setup_test_data.py
   - Test functions using `run_datahub_cmd` and `mce_helpers.check_golden_file`

3. **Generate golden file**:

   ```bash
   pytest tests/integration/<connector>/test_<connector>.py --update-golden-files -v
   ```

**When to Use Golden Files vs Structural Validation**:

- **Golden files**: Deterministic metadata (tables, views, schemas, containers)
- **Structural validation**: Dynamic data (job IDs, timestamps, execution-specific info)

Example structural validation:

```python
def test_with_dynamic_ids(runner, test_data, tmp_path):
    # Run ingestion...

    # Validate structure instead of exact match
    assert "dataFlow" in entity_types
    assert len(dataset_urns) >= 3
    assert any("expected_table" in u for u in dataset_urns)
```

**Handling Session-Scoped State**:
Some systems (like Flink's in-memory catalog) don't persist state across sessions. Solutions:

- Add `session_handle` config option to reuse existing sessions
- Use persistent catalog backends (Hive metastore, etc.)
- Create data in setup and keep session open for test

#### 🔴 ABSOLUTE BLOCKER: Verification Checklist Before Claiming "Tests Pass"

**If ANY of these items are not met, the code WILL BE REJECTED. No exceptions.**

Before concluding integration tests are complete, verify:

- [ ] Test environment is properly configured to test ALL connector features
- [ ] Test data includes at least 3-5 tables/datasets with various column types
- [ ] Test data includes views (if connector supports lineage)
- [ ] Golden file includes entity schemas (not just containers)
- [ ] Golden file includes lineage (if applicable)
- [ ] Test data is deterministic (same results on repeated runs)
- [ ] Running test twice produces identical golden files
- [ ] Integration test actually extracts metadata (check golden file size > 1KB)

**🔴 ABSOLUTE BLOCKER - Rule of thumb**: If your golden file is < 5KB or has < 20 metadata events, your integration test is INCOMPLETE and code will be REJECTED.

### 🔴 MANDATORY: Self-Evaluation of Integration Tests

**Before claiming integration tests are complete, you MUST perform this self-evaluation. Answer these questions honestly.**

#### Question 1: Test Environment Configuration

**Ask yourself**: "Is my test environment properly configured to test all the connector features I implemented?"

- ✅ **YES** - Test setup allows extracting all metadata types I'm testing (tables, views, schemas, lineage, etc.)
- ❌ **NO** - Test environment is missing configuration or data needed for full testing → **ABSOLUTE BLOCKER - MUST FIX**
- ❌ **UNSURE** - Check! Does the golden file contain all the metadata types the connector is supposed to extract?

**How to verify**:

- Check that test data/fixtures include all entity types your connector supports
- For SQL sources: Verify test database has tables, views, and relationships you're testing
- For API sources: Verify mock responses or test instance has all necessary data
- Run ingestion twice - results should be identical (determinism check)

#### Question 2: Golden File Content Quality

**Ask yourself**: "Does my golden file actually test what the connector does?"

Check your golden file (`*_mces_golden.json`):

- **File size**: Is it > 5KB? (< 5KB = probably incomplete)
- **Event count**: Does it have > 20 events? (< 20 = probably only containers)
- **Table schemas**: Can you see actual column definitions with types?
- **View lineage**: If connector supports views, are upstream references present?
- **Type mapping**: Do you see platform-specific types being mapped?

**Red flags** (ABSOLUTE BLOCKERS):

- ❌ File only contains container entities (catalogs, databases)
- ❌ No dataset (table/view) entities with schemas
- ❌ All events are `containerProperties` or `status` aspects
- ❌ No `schemaMetadata` aspects
- ❌ No `upstreamLineage` aspects (if connector supports lineage)

**Example of BAD golden file** (WILL BE REJECTED):

```json
[
  { "entityType": "container", "aspectName": "containerProperties" },
  { "entityType": "container", "aspectName": "status" },
  { "entityType": "container", "aspectName": "containerProperties" },
  { "entityType": "container", "aspectName": "status" }
]
```

**Why bad**: Only 4 events, only containers, no actual metadata!

**Example of GOOD golden file**:

```json
[
  {"entityType": "container", "aspectName": "containerProperties"},
  {"entityType": "dataset", "aspectName": "schemaMetadata", "aspect": {"fields": [...]}},
  {"entityType": "dataset", "aspectName": "datasetProperties"},
  {"entityType": "dataset", "aspectName": "upstreamLineage"},
  ... (20+ more events with real table/view metadata)
]
```

#### Question 3: Feature Coverage

**Ask yourself**: "Am I testing ALL the features I implemented?"

Go through your source code and check:

- [ ] **Tables extraction**: Do I have test tables? Are they in golden file?
- [ ] **Views extraction**: Did I implement views? Are test views in golden file?
- [ ] **Lineage extraction**: Did I implement lineage? Is it in golden file?
- [ ] **Type mapping**: Did I add custom types? Are they tested?
- [ ] **Container hierarchy**: Do containers have proper parent relationships?
- [ ] **Column-level lineage**: If implemented, is it tested?
- [ ] **Profiling**: If implemented, is it tested?

**Red flag**: If you implemented a feature but don't see it in the golden file → **INCOMPLETE TEST**

#### Question 4: Test Data Realism

**Ask yourself**: "Does my test data match what users will actually encounter?"

- ✅ **GOOD**: Multiple tables with different column types (INT, VARCHAR, TIMESTAMP, custom types)
- ✅ **GOOD**: Views that reference tables (for lineage testing)
- ✅ **GOOD**: Tables with foreign keys, constraints, indexes
- ✅ **GOOD**: Edge cases (special characters in names, NULL columns)
- ❌ **BAD**: One table with one column
- ❌ **BAD**: No views (if connector supports lineage)
- ❌ **BAD**: Only simple types (no custom types if platform has them)

#### Question 5: Test Determinism

**Ask yourself**: "If I run the test twice, do I get identical results?"

```bash
# Run test once
pytest tests/integration/<platform>/test_<platform>.py

# Run again immediately
pytest tests/integration/<platform>/test_<platform>.py

# Both should produce IDENTICAL golden files
```

**Red flags** (ABSOLUTE BLOCKERS):

- ❌ Timestamps in output change between runs → Use `@freeze_time`
- ❌ Random order of entities → Sort entities consistently
- ❌ Run IDs change → Use fixed test run ID
- ❌ Different results on second run → Test data is not persisting properly

#### Question 6: Honest Self-Assessment

**Ask yourself these hard questions**:

1. "Am I testing containers because it's easy, or testing actual metadata because it's thorough?"
   - If answer is "because it's easy" → **INCOMPLETE TEST**

2. "Would this integration test catch a bug in schema extraction?"
   - If NO → **INCOMPLETE TEST**

3. "Would this integration test catch a bug in type mapping?"
   - If NO → **INCOMPLETE TEST**

4. "If someone broke view lineage, would my test fail?"
   - If NO and connector supports lineage → **INCOMPLETE TEST**

5. "Am I comfortable submitting this for code review?"
   - If NO → **DO NOT PROCEED - FIX TESTS FIRST**

#### Question 7: Comparison with Production Sources

**Ask yourself**: "How does my test compare to existing DataHub sources?"

Pick a similar source and compare:

```bash
# Check their golden file size
ls -lh tests/integration/postgres/postgres_mces_golden.json
# Example: 147KB, 380 events

# Check your golden file size
ls -lh tests/integration/<platform>/<platform>_mces_golden.json
# If significantly smaller → investigate why
```

Look at their test setup:

- How is their test environment configured?
- How many test tables/entities do they create?
- Do they test views and lineage?
- What types do they test?

**If your test is significantly simpler than comparable sources → INCOMPLETE TEST**

### ⚠️ Common Self-Deception Patterns (Watch Out For These!)

**Pattern 1: "Tests are passing, so they must be good"**

- **Reality**: Tests can pass while testing nothing useful
- **Check**: What are they actually verifying? Just that code runs without errors?

**Pattern 2: "Golden file exists, so integration test is complete"**

- **Reality**: Golden file could be mostly empty containers
- **Check**: File size, event count, presence of table schemas

**Pattern 3: "I tested it manually in DataHub UI, so integration test is optional"**

- **Reality**: Manual testing doesn't prevent regressions
- **Check**: Is there automated regression prevention?

**Pattern 4: "Test environment is simple/minimal but test passes"**

- **Reality**: Minimal test setup may not properly test all connector features
- **Check**: Does test setup enable testing ALL implemented features? Run test twice, same results?

**Pattern 5: "I'll add better tests later before the PR"**

- **Reality**: Later never comes, incomplete tests get committed
- **Check**: Do NOT proceed to next phase without complete tests

### What Integration Tests MUST Verify

#### 1. Real Data Flow (Golden File Pattern)

```python
@freeze_time("2020-04-14 07:00:00")
def test_doris_ingestion_golden_file(doris_runner, pytestconfig, test_resources_dir, tmp_path):
    """Test complete ingestion against golden file"""

    config_file = (test_resources_dir / "doris_to_file.yml").resolve()
    run_datahub_cmd(["ingest", "-c", f"{config_file}"], tmp_path=tmp_path)

    # Verify against golden file
    mce_helpers.check_golden_file(
        pytestconfig,
        output_path=tmp_path / "doris_mces.json",
        golden_path=test_resources_dir / "doris_mces_golden.json",
    )
```

#### Generating/Updating Golden Files

**IMPORTANT**: To generate or update golden files, use the pytest `--update-golden-files` flag:

```bash
# Generate/update golden files for specific integration tests
pytest tests/integration/<platform>/test_<platform>.py --update-golden-files

# Example for Flink
pytest tests/integration/flink/test_flink.py --update-golden-files
```

**🔴 NEVER create custom scripts for generating golden files.** The `--update-golden-files` flag ensures:

- Consistency with the actual test execution flow
- Proper handling of test fixtures and setup
- Deterministic output matching what the tests verify

**Golden file must include**:

- Schema metadata for tables and views
- Custom type handling (HLL, BITMAP, ARRAY, JSONB for Doris)
- Lineage from view definitions
- Container hierarchy (database → schema → table)
- Tags, ownership, properties

#### 2. Connection Testing

```python
def test_connection_with_valid_credentials_succeeds(doris_runner):
    """Test that valid credentials allow connection"""
    report = test_connection_helpers.run_test_connection(
        DorisSource,
        {
            "host_port": "localhost:59030",
            "database": "dorisdb",
            "username": "root",
            "password": "",
        }
    )
    test_connection_helpers.assert_basic_connectivity_success(report)

def test_connection_with_wrong_port_fails(doris_runner):
    """Test that wrong port is detected"""
    report = test_connection_helpers.run_test_connection(
        DorisSource,
        {
            "host_port": "localhost:3306",  # MySQL port, not Doris
            "database": "dorisdb",
            "username": "root",
            "password": "",
        }
    )
    test_connection_helpers.assert_basic_connectivity_failure(
        report, "Connection refused"
    )

def test_connection_with_invalid_credentials_fails(doris_runner):
    """Test that invalid credentials are rejected"""
    report = test_connection_helpers.run_test_connection(
        DorisSource,
        {
            "host_port": "localhost:59030",
            "database": "dorisdb",
            "username": "wrong_user",
            "password": "wrong_pass",
        }
    )
    test_connection_helpers.assert_basic_connectivity_failure(
        report, "Access denied"
    )
```

#### 3. Feature-Specific Integration Tests

**🔴 ABSOLUTE BLOCKER: Lineage Integration Tests**

If your connector extracts lineage, you MUST have integration tests that verify lineage with REAL data:

- Test data must include views that reference tables
- Golden file must contain `UpstreamLineage` aspects
- For column-level lineage, verify `FineGrainedLineage` aspects are present

Unit tests for lineage registration (Pattern 6 above) are a MINOR requirement, but integration tests verifying actual lineage output are MANDATORY.

```python
def test_custom_types_extracted_from_real_database(doris_runner):
    """Test that Doris custom types are correctly extracted"""
    config = DorisConfig(
        host_port="localhost:59030",
        database="dorisdb",
        username="root",
        password=""
    )
    source = DorisSource(config, ctx)

    workunits = list(source.get_workunits())

    # Find the analytics table that has custom types
    analytics_wus = [wu for wu in workunits if "analytics" in wu.metadata.entityUrn]
    schema_aspect = analytics_wus[0].metadata.aspect

    # Verify custom types present
    field_types = {f.fieldPath: f.nativeDataType for f in schema_aspect.fields}
    assert "HLL" in field_types.values()
    assert "BITMAP" in field_types.values()
    assert "ARRAY" in field_types.values()

def test_view_lineage_extracted_from_real_database(doris_runner):
    """Test that view lineage is correctly extracted from Doris"""
    config = DorisConfig(
        host_port="localhost:59030",
        database="dorisdb",
        username="root",
        password="",
        include_view_lineage=True
    )
    source = DorisSource(config, ctx)

    workunits = list(source.get_workunits())

    # Find lineage for user_summary view
    lineage_wus = [wu for wu in workunits
                   if "user_summary" in wu.metadata.entityUrn
                   and "UpstreamLineage" in str(type(wu.metadata.aspect))]

    assert len(lineage_wus) > 0

    upstreams = lineage_wus[0].metadata.aspect.upstreams
    assert len(upstreams) == 2  # Should reference users and orders tables

    upstream_names = {u.dataset.split(",")[1] for u in upstreams}
    assert any("users" in name for name in upstream_names)
    assert any("orders" in name for name in upstream_names)
```

#### 4. Cross-Source Lineage Integration Tests

**🔴 ABSOLUTE BLOCKER: Cross-Source Lineage Tests Must Use REAL Ingestion Output**

When testing lineage that spans multiple sources (e.g., Kafka → Flink → Iceberg), you MUST:

1. **Run actual ingestions** from each source and capture real MCPs
2. **Never fabricate test data** - tests that create fake MCPs test nothing
3. **Use existing test infrastructure** - if a demo/test setup exists, USE IT

**❌ BAD - Fabricated Test Data (TESTS NOTHING - WILL BE REJECTED)**:

```python
# This test is WORTHLESS - it tests fake data against fake expectations
@pytest.fixture
def kafka_mcps():
    # Fabricated data - NOT from actual Kafka ingestion
    return [
        {"entityUrn": "urn:li:dataset:(urn:li:dataPlatform:kafka,events,PROD)", ...}
    ]

@pytest.fixture
def flink_mcps():
    # Fabricated data - NOT from actual Flink ingestion
    return [
        {"entityUrn": "urn:li:dataset:(urn:li:dataPlatform:flink,kafka_events,PROD)", ...}
    ]

def test_kafka_to_flink_lineage(kafka_mcps, flink_mcps):
    # This tests NOTHING - just that your fake data matches your fake expectations
    assert some_urn in kafka_mcps  # ❌ Circular logic
```

**Why This Is Bad**:

- You're testing that your fabricated URNs match your fabricated assertions
- Zero confidence that actual sources generate compatible URNs
- If Kafka source changes URN format, this test won't catch it
- Complete waste of maintenance effort

**✅ GOOD - Test With Real Ingestion Output**:

```python
@pytest.fixture(scope="module")
def streaming_demo_runner(docker_compose_runner, pytestconfig):
    """Start Kafka, Flink, Iceberg via docker-compose."""
    test_dir = pytestconfig.rootpath / "tests/integration/flink/streaming-demo"
    with docker_compose_runner(test_dir / "docker-compose.yml", "streaming") as services:
        wait_for_port(services, "kafka", 9092)
        wait_for_port(services, "flink-jobmanager", 8083)
        wait_for_port(services, "iceberg-rest", 8181)
        # Run setup script to create tables, views, streaming jobs
        subprocess.run([sys.executable, str(test_dir / "setup_streaming_demo.py")])
        yield services

@pytest.fixture
def kafka_mcps(streaming_demo_runner, tmp_path):
    """Run ACTUAL Kafka ingestion and return real MCPs."""
    output_file = tmp_path / "kafka_mces.json"
    run_datahub_cmd(["ingest", "-c", "kafka_recipe.yml", "--output", str(output_file)])
    with open(output_file) as f:
        return json.load(f)

@pytest.fixture
def flink_mcps(streaming_demo_runner, tmp_path):
    """Run ACTUAL Flink ingestion and return real MCPs."""
    output_file = tmp_path / "flink_mces.json"
    run_datahub_cmd(["ingest", "-c", "flink_recipe.yml", "--output", str(output_file)])
    with open(output_file) as f:
        return json.load(f)

def test_flink_references_correct_kafka_urns(kafka_mcps, flink_mcps):
    """Verify Flink's upstream references match actual Kafka URNs."""
    # Get URNs that Kafka source ACTUALLY generates
    kafka_urns = {mcp["entityUrn"] for mcp in kafka_mcps if "dataset" in mcp.get("entityType", "")}

    # Get URNs that Flink references as upstream
    flink_upstream_refs = set()
    for mcp in flink_mcps:
        if mcp.get("aspectName") == "upstreamLineage":
            for upstream in mcp["aspect"]["json"].get("upstreams", []):
                if "kafka" in upstream["dataset"]:
                    flink_upstream_refs.add(upstream["dataset"])

    # Verify Flink's references actually exist in Kafka output
    for ref in flink_upstream_refs:
        assert ref in kafka_urns, f"Flink references {ref} but Kafka generates {kafka_urns}"
```

**Key Principle**: The test MUST run actual ingestions and compare their real outputs. This catches:

- URN format mismatches between sources
- Platform instance inconsistencies
- Environment mismatches (PROD vs DEV)
- Dataset name formatting differences

**When to Write Cross-Source Lineage Tests**:

- Connector emits lineage to external platforms (Kafka, Iceberg, JDBC, etc.)
- Connector uses `explicit_lineage` or similar cross-platform references
- Data flows through multiple systems (streaming pipelines, ETL chains)

---

## Test Coverage Requirements

### Minimum Coverage by Category

**Unit Tests** (must cover ≥80% of source code):

- ✅ All data transformation logic
- ✅ All error handling paths
- ✅ All filtering/pattern matching
- ✅ All configuration validation
- ✅ All custom type handling
- ✅ All edge cases

**Integration Tests** (must exist):

- ✅ Golden file test (end-to-end)
- ✅ Connection test (valid credentials)
- ✅ Connection test (invalid credentials)
- ✅ Feature-specific tests (lineage, profiling, custom types)

**What NOT to Count Toward Coverage**:

- ❌ Tests of default values
- ❌ Tests of trivial getters
- ❌ Tests of framework behavior
- ❌ Tests that only verify mocks were called

---

## Test Quality Checklist

Before submitting PR, verify:

- [ ] **No tests of default configuration values** - All config tests verify validation logic, not defaults
- [ ] **No tests of trivial getters/setters** - All tests verify business logic with real behavior
- [ ] **All custom functionality has tests** - Custom types, error handling, filtering all tested
- [ ] **Error paths are tested** - Connection failures, permission errors, malformed data all tested
- [ ] **Edge cases are tested** - Empty results, missing data, boundary conditions tested
- [ ] **Integration tests use real database** - No mocking of database/API in integration tests
- [ ] **Golden file is comprehensive** - Includes all entity types, custom types, lineage
- [ ] **Tests are deterministic** - Use `@freeze_time` for timestamps, no random data
- [ ] **Tests are independent** - Each test can run alone, no shared state
- [ ] **Tests have descriptive names** - Name describes what behavior is tested, not implementation

---

## Example: Complete Test Suite for Doris Connector

See the examples above integrated into a complete test suite structure:

```
tests/
├── unit/
│   └── test_doris_source.py
│       ├── test_view_definition_sql_extraction()
│       ├── test_column_fetch_failure_continues_ingestion()
│       ├── test_table_pattern_filtering_respects_config()
│       ├── test_profiling_disabled_when_no_select_permission()
│       ├── test_empty_database_returns_no_workunits()
│       ├── test_table_with_no_columns_handled_gracefully()
│       ├── test_invalid_port_rejected()
│       └── test_doris_default_port_differs_from_mysql()
│
└── integration/
    └── doris/
        ├── docker-compose.yml
        ├── setup/
        │   └── setup.sql
        └── test_doris.py
            ├── test_doris_ingestion_golden_file()
            ├── test_connection_with_valid_credentials_succeeds()
            ├── test_connection_with_wrong_port_fails()
            ├── test_connection_with_invalid_credentials_fails()
            ├── test_custom_types_extracted_from_real_database()
            └── test_view_lineage_extracted_from_real_database()
```

**Total**: ~14 meaningful tests covering all business logic and edge cases.

---

## Summary: Testing Is Code Quality

**Remember**:

1. Tests must verify BUSINESS LOGIC, not framework behavior
2. Every test must be able to fail for a REAL reason
3. If removing the test doesn't reduce confidence, DELETE IT
4. Integration tests verify end-to-end with REAL dependencies
5. Golden files must be COMPREHENSIVE, not minimal

**Poor tests are worse than no tests** - they give false confidence and waste maintenance effort.

---

## 🔴 Expected Aspects - Golden File Verification

**Golden files MUST include all relevant aspects for the source type. Missing aspects indicate INCOMPLETE implementation.**

### Required Aspects by Source Type

For detailed aspect requirements, see:

- **SQL Database Sources**: [sql.md - Required Aspects](sql.md#required-aspects-for-sql-database-sources)
- **API-Based Sources**: [api.md - Required Aspects](api.md#required-aspects-for-api-based-sources)

### Key Rules

1. **`dataPlatformInstance` is ALWAYS required** - Not just when `platform_instance` is configured. It links every entity to its data platform URN.

2. **`browsePathsV2` and `status` are auto-generated** - These are automatically added by the pipeline from `container` aspects and don't need to be explicitly emitted. However, they MUST appear in golden files (which capture final output).

3. **Emit what the source provides** - If the source system has tags, ownership, or other metadata available, you MUST extract and emit it.

### Quick Verification Script

To verify your golden file has expected aspects:

```bash
python3 -c "
import json
with open('tests/integration/<platform>/<platform>_mces_golden.json') as f:
    data = json.load(f)
aspects = set()
for item in data:
    if 'proposedSnapshot' in item:
        for aspect in item['proposedSnapshot'].get('aspects', []):
            aspects.update(aspect.keys())
    elif 'aspectName' in item:
        aspects.add(item['aspectName'])
print('Aspects found:', sorted(aspects))
"
```

**Compare against the expected aspects in the source-type-specific documentation. If required aspects are missing, your implementation is INCOMPLETE.**

---

## 🔴 Final Checklist: Before Claiming Tests Are Complete

**STOP and perform this checklist. Answer YES or NO to each question.**

### Absolute Blockers (Must ALL be YES)

- [ ] **NO trivial tests** - I have ZERO tests that check defaults, getters, or obvious equality
- [ ] **NO anti-pattern tests** - I have ZERO tests that verify framework behavior
- [ ] **Golden file > 5KB** - My golden file is larger than 5KB
- [ ] **Golden file > 20 events** - My golden file has more than 20 metadata events
- [ ] **Schemas in golden file** - My golden file contains `schemaMetadata` aspects with column definitions
- [ ] **Test environment properly configured** - My test setup enables testing all connector features
- [ ] **Test runs twice** - Running integration test twice produces IDENTICAL results
- [ ] **All features tested** - Every feature I implemented appears in the golden file

### Self-Evaluation Complete

- [ ] **Answered Question 1** - Test environment configuration verified
- [ ] **Answered Question 2** - Golden file content quality checked
- [ ] **Answered Question 3** - Feature coverage confirmed
- [ ] **Answered Question 4** - Test data realism assessed
- [ ] **Answered Question 5** - Test determinism verified
- [ ] **Answered Question 6** - Honest self-assessment completed
- [ ] **Answered Question 7** - Comparison with production sources done

### Code Quality

- [ ] **Tests verify logic** - All unit tests verify business logic (transformation, error handling, filtering)
- [ ] **Tests don't verify trivia** - No tests for config defaults or simple getters
- [ ] **Integration test is realistic** - Test data matches production scenarios
- [ ] **Compared to similar sources** - My test is similar in scope to comparable DataHub sources

**If ANY checkbox above is unchecked → Tests are INCOMPLETE → DO NOT PROCEED**

---

## When Tests Are Truly Complete

You know your tests are complete when:

✅ You can confidently say: "This test would catch real bugs in schema extraction, type mapping, and lineage"

✅ Your golden file is comparable in size/content to similar DataHub sources

✅ You've performed the self-evaluation and answered all 7 questions honestly

✅ Your test data persists across container restarts

✅ Running the test multiple times produces identical results

✅ You have ZERO trivial or anti-pattern tests

**Only then should you proceed to documentation and final PR preparation.**
