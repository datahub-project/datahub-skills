# Performance & Scalability Review Deep Dive

Check against `standards/performance.md` for optimization patterns.

---

## Context Gathering

```bash
# Find iteration patterns
grep -rn "for.*in.*:" src/datahub/ingestion/source/<connector>/*.py | head -20

# Find yield vs return patterns
grep -rn "yield\|return \[" src/datahub/ingestion/source/<connector>/*.py

# Find query patterns
grep -rn "execute\|query\|fetch" src/datahub/ingestion/source/<connector>/*.py

# Find caching patterns
grep -rn "cache\|@lru_cache\|FileBackedDict" src/datahub/ingestion/source/<connector>/*.py
```

---

## N+1 Query Pattern Detection

**Critical anti-pattern**: One query per entity instead of batching.

```python
# N+1 Pattern - flag this
for table in tables:
    columns = self._get_columns(table)  # Query per table!

# Batched Pattern - good
all_columns = self._get_all_columns_for_schema(schema)  # Single query
columns_by_table = group_by(all_columns, key=lambda c: c.table_name)
for table in tables:
    columns = columns_by_table.get(table.name, [])
```

**Check for N+1 patterns in:**

- [ ] Column fetching (per table vs per schema)
- [ ] Metadata lookups (user info, project info, etc.)
- [ ] Foreign key/relationship resolution
- [ ] Tag/label fetching

---

## Memory Management

```
Streaming & Generators:
[ ] Uses yield for workunit emission (not building lists)
[ ] No accumulating large lists in memory
[ ] Proper cleanup of resources after use

Large Collection Handling:
[ ] Uses FileBackedDict for collections >5,000 items (if applicable)
[ ] No unbounded growth of in-memory caches
[ ] Pagination for large API responses
```

---

## Extraction Efficiency Analysis

**Evaluate how metadata is extracted:**

| Entity Type | Extraction Method                    | Scalability Assessment       |
| ----------- | ------------------------------------ | ---------------------------- |
| Tables      | [per-schema batch / per-table query] | [Good / N+1 risk]            |
| Columns     | [bulk fetch / per-table query]       | [Good / N+1 risk]            |
| Lineage     | [SQL parsing / API calls]            | [Good / Scalability concern] |
| Tags/Labels | [batch / per-entity]                 | [Good / N+1 risk]            |

**Key questions:**

- How many API calls/queries for 1,000 tables?
- Does extraction scale linearly or quadratically?
- Are there obvious bottlenecks?

---

## API & Query Optimization

```
For SQL Sources:
[ ] Bulk queries for metadata (INFORMATION_SCHEMA style)
[ ] Efficient schema introspection
[ ] Connection pooling/reuse
[ ] No SELECT * when specific columns suffice

For API Sources:
[ ] HTTP session reuse (not creating new connections per request)
[ ] Proper pagination implementation
[ ] Rate limiting consideration
[ ] Batch endpoints used where available
[ ] Retry logic for transient failures
```

---

## Caching Patterns

```
Appropriate Caching:
[ ] @lru_cache for repeated lookups with same inputs
[ ] Registry pattern for reference data (users, projects)
[ ] No redundant fetches of the same data

Caching Anti-Patterns:
[ ] Caching mutable data that could change
[ ] Unbounded cache growth
[ ] Missing cache for frequently accessed lookups
```

---

## Parallel Processing Readiness

```
Thread-Safety (if parallelism used or planned):
[ ] Worker functions are self-contained
[ ] No shared mutable state between workers
[ ] Connection handling is thread-safe
[ ] max_workers config option available

Design for Future Optimization:
[ ] Processing at schema/container level (easy to parallelize)
[ ] Data fetching in separate methods (easy to batch later)
[ ] Clear boundaries between independent units of work
```

---

## Performance Checklist Summary

```
Essential (Always Required):
[ ] Uses generators (yield) for workunit emission
[ ] Implements pagination for API calls
[ ] HTTP session reuse (API sources)
[ ] No obvious N+1 query patterns

Recommended (For Production Quality):
[ ] Batch queries when fetching for multiple entities
[ ] Config options for tuning (batch_size, max_workers)
[ ] Structured for future parallelization

Scale-Dependent (When Needed):
[ ] FileBackedDict for large collections
[ ] ThreadedIteratorExecutor for parallel processing
[ ] Advanced caching strategies
```

---

## Performance Review Output

When reporting performance findings:

- Estimate impact: "1,000 tables = ~1,000 queries" vs "1,000 tables = ~10 queries"
- Provide scalability assessment: "Scales linearly" / "O(n^2) concern"
- Suggest specific optimizations with code examples
- Note if optimization is blocking vs nice-to-have based on expected scale

---

## Performance Anti-Patterns to Flag

| Anti-Pattern                       | Impact                        | Fix                      |
| ---------------------------------- | ----------------------------- | ------------------------ |
| N+1 queries                        | 100x slower for large schemas | Batch queries per schema |
| Building lists instead of yielding | Memory exhaustion             | Use `yield`              |
| New HTTP connection per request    | 2-3x slower                   | Reuse session            |
| No pagination                      | Timeout/memory issues         | Implement pagination     |
| Query per column                   | Extremely slow                | Bulk column fetch        |
| Unbounded in-memory cache          | Memory exhaustion             | FileBackedDict or LRU    |
