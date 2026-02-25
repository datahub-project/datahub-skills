# Testing Patterns for DataHub Connectors

This guide provides patterns and examples for writing tests for DataHub connectors.

## Unit Test Structure

### SQL Connector Unit Tests

Standard imports and fixtures for SQL-based connectors:

```python
# tests/unit/test_<source>_source.py
from unittest.mock import MagicMock, Mock, patch
import pytest

from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.source.<source>.config import <Source>Config
from datahub.ingestion.source.<source>.source import <Source>Source

# For two-tier sources (schema = database)
from datahub.ingestion.source.sql.two_tier_sql_source import TwoTierSQLAlchemySource

# For three-tier sources (database > schema > table)
from datahub.ingestion.source.sql.sql_common import SQLAlchemySource


@pytest.fixture
def config():
    return <Source>Config(
        # Minimal required config for instantiation
    )


@pytest.fixture
def source(config):
    ctx = PipelineContext(run_id="test-run")
    return <Source>Source(config=config, ctx=ctx)
```

### API Connector Unit Tests

```python
# tests/unit/test_<source>_source.py
from unittest.mock import MagicMock, patch
import pytest

from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.source.<source>.config import <Source>Config
from datahub.ingestion.source.<source>.source import <Source>Source


@pytest.fixture
def mock_client():
    """Mock the API client to avoid real network calls."""
    with patch("datahub.ingestion.source.<source>.client.<Source>Client") as mock:
        yield mock.return_value
```

## Coverage Guidance

### Thresholds

- **Minimum:** 80% line coverage
- **Target:** 85-90% for production connectors

### What Uncovered Lines Are Acceptable

Coverage excludes these categories (they don't indicate missing tests):

1. **Import error handling** - `try/except ImportError` blocks for optional dependencies
2. **Framework internals** - Context manager `__enter__`/`__exit__`, abstract method stubs
3. **Defensive guards** - `if value is None: return` where None is impossible in practice
4. **Type narrowing** - `assert isinstance()` for mypy satisfaction

### What MUST Be Covered

- All public methods with business logic
- Configuration validation and defaults
- Entity extraction and transformation
- Error paths that users might encounter

### Running Coverage

```bash
pytest tests/unit/test_<source>_source.py \
    --cov=src/datahub/ingestion/source/<source> \
    --cov-report=term-missing
```

## Golden File Validation

### Minimum Content

Golden files must contain:

- At least 2 tables with schema metadata
- At least 1 view (if source supports views)
- Container hierarchy (database/schema containers)
- If lineage claimed: at least 1 upstream lineage edge

### Expected Output Sizes

| Test Scenario            | Expected Records | File Size |
| ------------------------ | ---------------- | --------- |
| Basic (2 tables, 1 view) | 15-25            | 15-30 KB  |
| With profiling           | 25-40            | 30-60 KB  |
| With lineage             | 20-35            | 25-50 KB  |

### Validating Golden Files

Use the `validate-golden-files.py` script or these jq commands.

**Important:** SQL connectors often use **MCE format** (not MCP). Check both!

```bash
# Count datasets (MCE format)
jq '[.[] | select(.proposedSnapshot."com.linkedin.pegasus2avro.metadata.snapshot.DatasetSnapshot")] | length' golden.json

# Count schema metadata (MCE format - nested in snapshot)
jq '[.[] | select(.proposedSnapshot) | .proposedSnapshot."com.linkedin.pegasus2avro.metadata.snapshot.DatasetSnapshot".aspects[] | select(."com.linkedin.pegasus2avro.schema.SchemaMetadata")] | length' golden.json

# Count lineage (often in MCP format)
jq '[.[] | select(.aspectName=="upstreamLineage")] | length' golden.json

# Count containers
jq '[.[] | select(.entityType=="container")] | length' golden.json
```

## Test Prioritization

When adding tests, prioritize in this order:

### Priority 1: Must Have

- [ ] Config instantiation with minimal required fields
- [ ] Config validation rejects invalid inputs
- [ ] Basic extraction produces expected entity types
- [ ] Schema metadata has correct column types

### Priority 2: Should Have

- [ ] Platform-specific type handling (arrays, JSON, etc.)
- [ ] View extraction (if supported)
- [ ] Lineage extraction (if claimed as capability)
- [ ] Container hierarchy is correct

### Priority 3: Nice to Have

- [ ] Empty database handling
- [ ] Unicode in table/column names
- [ ] Very long identifiers
- [ ] Special characters in names

### Anti-Patterns to Avoid

- Don't test that `@Nonnull` parameters reject null (framework's job)
- Don't test exact error message wording (brittle)
- Don't test Lombok-generated code
- Don't test framework behavior (SQLAlchemy, Pydantic)

## Inspector Method Wrapping

When overriding SQLAlchemy inspector methods, use `setattr()` to avoid mypy errors:

```python
# ❌ BAD - Direct assignment fails mypy
inspector.get_columns = wrapper_function

# ✅ GOOD - Use setattr() for dynamic replacement
setattr(inspector, 'get_columns', wrapper_function)
```

## See Also

- [MCE vs MCP Formats](./mce-vs-mcp-formats.md)
- [Two-Tier vs Three-Tier Sources](./two-tier-vs-three-tier.md)
