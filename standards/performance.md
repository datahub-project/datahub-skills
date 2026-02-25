# Performance and Memory Optimization

This guide covers performance optimization patterns for DataHub connectors. These are **recommendations**, not requirements - simplicity and correctness should come first.

## Philosophy: Start Simple, Optimize Later

**Key Principle**: Write simple, correct code first. Add performance optimizations only when needed.

Most connectors don't need advanced performance tuning. The patterns in this guide become relevant when:

- Your source has **10,000+ entities** (tables, dashboards, etc.)
- Ingestion takes **longer than 30 minutes**
- You observe **memory issues** during ingestion
- Users report **timeout or rate limiting** problems

**If your connector works well without these optimizations, that's perfectly fine.** Simple code is easier to maintain, test, and debug.

---

## Related Guides

- [Main Guide](main.md) - Overview and planning
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [Patterns](patterns.md) - General implementation patterns
- [SQL Sources](sql.md) - SQL-specific patterns
- [API-Based Sources](api.md) - REST/GraphQL API patterns
- [Testing](testing.md) - Testing strategies

---

## Table of Contents

1. [When to Optimize](#when-to-optimize)
2. [Query and API Optimization](#query-and-api-optimization)
3. [Memory Management](#memory-management)
4. [Parallel Processing](#parallel-processing)
5. [Caching Patterns](#caching-patterns)
6. [Request Optimization](#request-optimization)
7. [Designing for Future Optimization](#designing-for-future-optimization)

---

## When to Optimize

### Signs You Need Performance Work

| Symptom                | Likely Cause                        | Recommended Pattern                             |
| ---------------------- | ----------------------------------- | ----------------------------------------------- |
| Ingestion takes hours  | N+1 queries or sequential API calls | [Batch queries](#batch-query-patterns)          |
| Memory errors (OOM)    | Loading all entities into memory    | [FileBackedDict](#filebacked-collections)       |
| Rate limiting errors   | Too many API calls                  | [Request batching](#request-batching)           |
| Slow for large schemas | Per-table queries                   | [Bulk metadata loading](#bulk-metadata-loading) |

### When NOT to Optimize

**Keep it simple when:**

- Source has fewer than 1,000 entities
- Ingestion completes in under 10 minutes
- No memory or timeout issues reported
- You're building the initial version

**Example**: A connector for a small BI tool with 50 dashboards doesn't need parallel processing or file-backed storage. Simple sequential iteration is fine.

---

## Query and API Optimization

### The N+1 Query Problem

**What it is**: Making one query per entity instead of batching.

**Impact**: 1,000 tables = 1,000 queries instead of 1 query. This can make ingestion 10-100x slower.

#### Simple Approach (Start Here)

For most connectors, sequential queries are fine:

```python
# ✅ Simple and correct - start with this
def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
    for schema in self._get_schemas():
        for table in self._get_tables(schema):
            # One query per table - simple but may be slow for large schemas
            columns = self._get_columns(table)
            yield self._create_table_workunit(table, columns)
```

**When this is sufficient:**

- Fewer than 500 tables
- Source API is fast
- No performance complaints

#### Optimized Approach (Add When Needed)

If you need better performance, batch your queries:

```python
# ✅ Optimized - bulk fetch then filter in memory
def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
    for schema in self._get_schemas():
        # Fetch ALL columns for schema in one query
        all_columns = self._get_all_columns_for_schema(schema)
        columns_by_table = self._group_by_table(all_columns)

        for table in self._get_tables(schema):
            columns = columns_by_table.get(table.name, [])
            yield self._create_table_workunit(table, columns)

def _get_all_columns_for_schema(self, schema: str) -> List[ColumnInfo]:
    """Fetch all columns for a schema in a single query."""
    query = f"""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
    """
    return self.connection.execute(query)
```

**Key difference**: One query per schema instead of one query per table.

### Batch Query Patterns

#### Pattern: Bulk Loading with In-Memory Filtering

**When to use**: SQL sources with many tables per schema.

```python
class MyDatabaseSource(Source):
    def __init__(self, config, ctx):
        super().__init__(ctx)
        self.config = config
        # Cache for bulk-loaded metadata
        self._tables_cache: Dict[str, List[TableInfo]] = {}
        self._columns_cache: Dict[str, List[ColumnInfo]] = {}

    def _ensure_schema_loaded(self, schema: str) -> None:
        """Load all metadata for a schema if not already cached."""
        if schema in self._tables_cache:
            return

        # Single query gets all tables
        self._tables_cache[schema] = self._bulk_fetch_tables(schema)
        # Single query gets all columns
        self._columns_cache[schema] = self._bulk_fetch_columns(schema)

    def _get_tables(self, schema: str) -> List[TableInfo]:
        self._ensure_schema_loaded(schema)
        return [
            t for t in self._tables_cache[schema]
            if self.config.table_pattern.allowed(t.name)
        ]

    def _get_columns(self, schema: str, table: str) -> List[ColumnInfo]:
        self._ensure_schema_loaded(schema)
        return [
            c for c in self._columns_cache[schema]
            if c.table_name == table
        ]
```

**Benefits:**

- Single query per schema (not per table)
- Filtering happens in memory (fast)
- Easy to add to existing connectors

#### Pattern: WHERE IN Batching

**When to use**: When you need to fetch details for a known list of entities.

```python
# ❌ N+1 pattern - one query per ID
for table_id in table_ids:
    details = api.get_table_details(table_id)  # N queries!

# ✅ Batch pattern - one query for all IDs
def _get_table_details_batch(self, table_ids: List[str]) -> Dict[str, TableDetails]:
    """Fetch details for multiple tables in one call."""
    if not table_ids:
        return {}

    # SQL example
    query = f"""
        SELECT * FROM table_metadata
        WHERE table_id IN ({','.join(f"'{id}'" for id in table_ids)})
    """
    results = self.connection.execute(query)
    return {r.table_id: r for r in results}

# Usage
details_map = self._get_table_details_batch(table_ids)
for table_id in table_ids:
    details = details_map.get(table_id)
    # Process...
```

### API Pagination

For API sources, always implement proper pagination:

```python
def _get_all_datasets(self) -> Iterable[Dataset]:
    """Fetch all datasets with pagination."""
    page_token = None

    while True:
        response = self.client.list_datasets(
            page_size=100,
            page_token=page_token
        )

        for dataset in response.datasets:
            yield dataset

        page_token = response.next_page_token
        if not page_token:
            break
```

---

## Memory Management

### When Memory Matters

Memory optimization becomes important when:

- Dealing with **10,000+ entities**
- Entities have **large metadata** (many columns, long descriptions)
- Running in **memory-constrained environments**

For smaller sources, standard Python data structures work fine.

### Streaming with Generators

**Always use generators** - this is a best practice regardless of scale:

```python
# ✅ GOOD - Streaming with generators
def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
    for table in self._get_tables():
        yield self._create_workunit(table)  # Memory released after processing

# ❌ BAD - Loading all into memory first
def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
    all_workunits = []
    for table in self._get_tables():
        all_workunits.append(self._create_workunit(table))
    return all_workunits  # All in memory at once
```

**This pattern costs nothing** and prevents memory issues as your source scales.

### FileBackedDict for Large Collections

**When to use**: Collections with more than ~5,000 items that you need to keep in memory.

**What it does**: Stores data on disk instead of RAM, loading items on-demand.

```python
from datahub.utilities.file_backed_collections import FileBackedDict, FileBackedList

class LargeScaleSource(Source):
    def __init__(self, config, ctx):
        super().__init__(ctx)
        # Use file-backed storage for large collections
        self._table_schemas: FileBackedDict[str, SchemaInfo] = FileBackedDict()
        self._processed_tables: FileBackedList[str] = FileBackedList()

    def _cache_schema(self, table_urn: str, schema: SchemaInfo) -> None:
        """Cache schema info - stored on disk, not RAM."""
        self._table_schemas[table_urn] = schema

    def _get_cached_schema(self, table_urn: str) -> Optional[SchemaInfo]:
        """Retrieve cached schema - loaded from disk on demand."""
        return self._table_schemas.get(table_urn)
```

**Memory comparison** (example with 10,000 stored procedures):

- Standard dict: ~500 MB RAM
- FileBackedDict: ~50 MB RAM

**When NOT to use:**

- Collections smaller than 1,000 items
- Items accessed only once (just use generators)
- Performance is critical (disk I/O adds latency)

### Designing for Memory Efficiency

**Start simple, add file-backing later if needed:**

```python
class MySource(Source):
    def __init__(self, config, ctx):
        super().__init__(ctx)

        # Start with simple dict - easy to understand and test
        # Switch to FileBackedDict if memory becomes an issue
        self._metadata_cache: Dict[str, Metadata] = {}

        # If you expect large scale from the start:
        # self._metadata_cache: FileBackedDict[str, Metadata] = FileBackedDict()
```

**Tip**: The interface is the same, so switching later is a one-line change.

---

## Parallel Processing

### When Parallelism Helps

Parallel processing helps when:

- Operations are **I/O-bound** (API calls, database queries)
- Operations are **independent** (no shared state)
- Single-threaded ingestion takes **more than 15 minutes**

**Parallelism does NOT help when:**

- Operations are CPU-bound (Python GIL limits benefit)
- Operations share state (need locks, adds complexity)
- Source has strict rate limits (parallel calls hit limits faster)

### Simple Approach: Sequential Processing

**Start with sequential processing** - it's simpler and easier to debug:

```python
# ✅ Simple sequential approach - start here
def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
    for schema in self._get_schemas():
        yield from self._process_schema(schema)

def _process_schema(self, schema: SchemaInfo) -> Iterable[MetadataWorkUnit]:
    for table in self._get_tables(schema):
        yield self._create_table_workunit(table)
```

### ThreadedIteratorExecutor (Add When Needed)

DataHub provides `ThreadedIteratorExecutor` for parallel processing:

```python
from datahub.utilities.threaded_iterator_executor import ThreadedIteratorExecutor

class OptimizedSource(Source):
    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        schemas = list(self._get_schemas())

        # Process schemas in parallel
        for wu in ThreadedIteratorExecutor.process(
            worker_func=self._process_schema_worker,
            args_list=[(schema,) for schema in schemas],
            max_workers=self.config.max_workers,  # Default: 10
        ):
            yield wu

    def _process_schema_worker(self, schema: SchemaInfo) -> Iterable[MetadataWorkUnit]:
        """Worker function - must be thread-safe."""
        for table in self._get_tables(schema):
            yield self._create_table_workunit(table)
```

**Benefits:**

- Results streamed as completed (low memory)
- Configurable worker count
- Handles exceptions gracefully

**Considerations:**

- Worker function must be thread-safe
- Don't share mutable state between workers
- Consider rate limits when setting `max_workers`

### Making Code Thread-Safe

If you plan to add parallelism later, design with thread-safety in mind:

```python
# ✅ Thread-safe: Each call creates its own connection
def _get_tables(self, schema: str) -> List[TableInfo]:
    with self._create_connection() as conn:
        return conn.query(f"SELECT * FROM tables WHERE schema = '{schema}'")

# ❌ Not thread-safe: Shared connection
def _get_tables(self, schema: str) -> List[TableInfo]:
    return self.connection.query(...)  # self.connection is shared!
```

### Configuration for Parallelism

Add parallelism as an optional config:

```python
class MySourceConfig(StatefulIngestionConfigBase):
    # Default to sequential (simple)
    max_workers: int = Field(
        default=1,
        description=(
            "Number of parallel workers for metadata extraction. "
            "Set to 1 for sequential processing (default, simpler). "
            "Increase for faster ingestion of large sources."
        )
    )
```

---

## Caching Patterns

### When Caching Helps

Caching is useful when:

- Same data is accessed multiple times
- Fetching data is expensive (slow API, complex query)
- Data doesn't change during ingestion

### Simple Function Caching

Python's `@lru_cache` works well for simple cases:

```python
from functools import lru_cache

class MySource(Source):
    @lru_cache(maxsize=128)
    def _get_platform_name(self, connection_type: str) -> str:
        """Map connection type to platform - called many times, same result."""
        return PLATFORM_MAP.get(connection_type, "unknown")

    @lru_cache(maxsize=1)
    def _get_database_info(self) -> DatabaseInfo:
        """Fetch database info once and cache it."""
        return self.client.get_database_info()
```

**When to use `@lru_cache`:**

- Pure functions (same input → same output)
- Expensive operations called multiple times
- Data doesn't change during ingestion

**Limitations:**

- Arguments must be hashable
- Cache lives for connector lifetime
- Not thread-safe by default

### Registry Pattern for Lookups

For frequently accessed mappings, use a registry:

```python
class MySource(Source):
    def __init__(self, config, ctx):
        super().__init__(ctx)
        # Registries populated once, accessed many times
        self._user_registry: Dict[str, UserInfo] = {}
        self._project_registry: Dict[str, ProjectInfo] = {}

    def _populate_registries(self) -> None:
        """Fetch all reference data upfront."""
        # Single API call to get all users
        for user in self.client.list_users():
            self._user_registry[user.id] = user

        # Single API call to get all projects
        for project in self.client.list_projects():
            self._project_registry[project.id] = project

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        # Populate registries once at start
        self._populate_registries()

        for dataset in self._get_datasets():
            # Fast lookups from registry
            owner = self._user_registry.get(dataset.owner_id)
            project = self._project_registry.get(dataset.project_id)
            yield self._create_workunit(dataset, owner, project)
```

**Benefits:**

- Avoids N+1 lookups
- Simple to implement
- Easy to test

---

## Request Optimization

### Session Reuse

Reuse HTTP sessions for better performance:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class MyAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url

        # Create session with connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

        # Optional: Add retry logic for transient failures
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, endpoint: str) -> dict:
        response = self.session.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self.session.close()
```

**Benefits:**

- Connection pooling (faster subsequent requests)
- Automatic retry on transient failures
- Consistent headers

### Rate Limiting

If your source has rate limits, implement a simple limiter:

```python
import time

class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 10):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: Optional[float] = None

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

# Usage
class MySource(Source):
    def __init__(self, config, ctx):
        super().__init__(ctx)
        self.rate_limiter = RateLimiter(requests_per_second=5)

    def _api_call(self, endpoint: str) -> dict:
        self.rate_limiter.wait()  # Respect rate limit
        return self.client.get(endpoint)
```

### Request Batching

Some APIs support batch requests:

```python
# ❌ Individual requests
for dataset_id in dataset_ids:
    details = api.get_dataset(dataset_id)  # N requests

# ✅ Batch request (if API supports it)
details_list = api.get_datasets_batch(dataset_ids)  # 1 request
```

Check your source's API documentation for batch endpoints.

---

## Designing for Future Optimization

### Structure Code for Easy Enhancement

Even if you start simple, structure your code so optimizations can be added later:

```python
class MySource(Source):
    """Source that's designed to be optimized later."""

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        # Process at the schema level - easy to parallelize later
        for schema in self._get_schemas():
            yield from self._process_schema(schema)

    def _process_schema(self, schema: SchemaInfo) -> Iterable[MetadataWorkUnit]:
        """Process a single schema - self-contained, can run in parallel."""
        # All state for this schema is local
        tables = self._get_tables(schema)
        columns = self._get_columns_for_schema(schema)

        for table in tables:
            table_columns = [c for c in columns if c.table == table.name]
            yield self._create_workunit(table, table_columns)

    def _get_columns_for_schema(self, schema: str) -> List[ColumnInfo]:
        """Get columns - can be optimized to bulk fetch later."""
        # Simple version: query per table
        # Optimized version: single query for all tables in schema
        return self.connection.get_columns(schema)
```

**Why this structure helps:**

- `_process_schema` is self-contained (easy to parallelize)
- Data fetching is in separate methods (easy to batch later)
- No shared mutable state between schemas

### Add Optimization Flags

Make optimizations configurable:

```python
class MySourceConfig(StatefulIngestionConfigBase):
    # Performance tuning - optional
    max_workers: int = Field(
        default=1,
        description="Parallel workers. Default 1 (sequential) is fine for most cases."
    )

    batch_size: int = Field(
        default=100,
        description="Batch size for bulk operations. Increase for faster ingestion."
    )

    use_bulk_queries: bool = Field(
        default=False,
        description=(
            "Use bulk queries for metadata. Faster for large schemas, "
            "but may use more memory. Enable if ingestion is slow."
        )
    )
```

### Document Performance Characteristics

In your source documentation, note performance characteristics:

```python
class MySource(Source):
    """DataHub source for MyPlatform.

    Performance Notes:
    - Scales well up to ~10,000 tables with default settings
    - For larger deployments, consider enabling `use_bulk_queries`
    - Memory usage is approximately 1MB per 100 tables

    To optimize for large sources:
    - Set `max_workers: 4` for parallel schema processing
    - Set `use_bulk_queries: true` for faster metadata loading
    """
```

---

## Quick Reference

### When to Apply Each Pattern

| Pattern                | Apply When          | Complexity | Impact                     |
| ---------------------- | ------------------- | ---------- | -------------------------- |
| Generators (streaming) | **Always**          | Low        | Prevents memory issues     |
| Session reuse          | **Always** for HTTP | Low        | 2-3x faster requests       |
| Pagination             | **Always** for APIs | Low        | Required for large results |
| Batch queries          | >500 entities       | Medium     | 10-100x fewer queries      |
| FileBackedDict         | >5,000 entities     | Low        | 10x less memory            |
| Parallel processing    | >15 min ingestion   | Medium     | 2-5x faster                |
| LRU caching            | Repeated lookups    | Low        | Eliminates redundant calls |

### Performance Checklist

**Essential (always do):**

- [ ] Use generators (`yield`) for workunit emission
- [ ] Implement pagination for API calls
- [ ] Reuse HTTP sessions

**Recommended (if relevant):**

- [ ] Batch queries when fetching for multiple entities
- [ ] Add config options for tuning (`max_workers`, `batch_size`)
- [ ] Structure code for future parallelization

**When needed (based on scale):**

- [ ] Use `FileBackedDict` for large collections
- [ ] Add `ThreadedIteratorExecutor` for parallel processing
- [ ] Implement caching for repeated lookups

### Example: Connector Evolution

**Version 1 - Simple and correct:**

```python
def get_workunits_internal(self):
    for table in self._get_tables():
        yield self._create_workunit(table)
```

**Version 2 - Bulk loading added:**

```python
def get_workunits_internal(self):
    all_metadata = self._bulk_fetch_metadata()  # Single query
    for table in self._get_tables():
        yield self._create_workunit(table, all_metadata[table.name])
```

**Version 3 - Parallelism added:**

```python
def get_workunits_internal(self):
    schemas = list(self._get_schemas())
    for wu in ThreadedIteratorExecutor.process(
        worker_func=self._process_schema,
        args_list=[(s,) for s in schemas],
        max_workers=self.config.max_workers,
    ):
        yield wu
```

Each version builds on the previous, with minimal changes needed.

---

## Summary

1. **Start simple** - Write straightforward, correct code first
2. **Measure before optimizing** - Only optimize when you see actual problems
3. **Use generators** - This one pattern prevents most memory issues
4. **Design for enhancement** - Structure code so optimizations can be added later
5. **Make it configurable** - Let users tune performance for their scale
