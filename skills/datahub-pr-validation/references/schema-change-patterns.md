# Schema Change Patterns

Common schema changes and their downstream impact patterns.

## Column Removal

**Risk: Critical**

Removes a column that may be referenced by downstream consumers.

```sql
-- Before
SELECT customer_id, order_date, amount FROM raw_orders

-- After (customer_id removed)
SELECT order_date, amount FROM raw_orders
```

**Impact:** Any downstream model doing `SELECT customer_id` will fail.

**Check:**
```bash
datahub lineage --urn "<URN>" --direction downstream --hops 2 --format json
```

Look for downstream entities that reference the removed column in their definitions.

## Column Rename

**Risk: Critical**

Renames a column, which is equivalent to remove + add from downstream perspective.

```sql
-- Before
SELECT customer_id FROM raw_orders

-- After
SELECT cust_id FROM raw_orders
```

**Impact:** Same as column removal — all downstream references to old name break.

**Migration:** Requires coordinated rename across all downstream models.

## Type Change

**Risk: High**

Changes the data type of a column (e.g., VARCHAR to INT, DATE to TIMESTAMP).

```sql
-- Before
order_date DATE

-- After
order_date TIMESTAMP
```

**Impact:** Downstream joins, comparisons, and aggregations may behave unexpectedly or fail.

**Check:** Verify downstream models don't assume the original type.

## New NOT NULL Constraint

**Risk: High**

Adds a NOT NULL constraint to a previously nullable column.

```sql
-- Before
customer_id VARCHAR NULL

-- After
customer_id VARCHAR NOT NULL
```

**Impact:** Downstream inserts that expect nulls will fail.

## Column Addition

**Risk: Medium**

Adds a new column (generally backward compatible).

```sql
-- Before
SELECT order_date, amount FROM raw_orders

-- After
SELECT order_date, amount, tax_amount FROM raw_orders
```

**Impact:** Generally safe, but check for `SELECT *` consumers that may get unexpected data.

## Table/View Removal

**Risk: Critical**

Removes a table or view that downstream entities depend on.

**Impact:** All downstream queries against this entity will fail.

**Check:** Must have 0 downstream dependencies or provide migration path.

## Logic Change (No Schema Change)

**Risk: Medium-High**

Changes transformation logic without altering schema.

```sql
-- Before
SUM(amount) as total

-- After
SUM(CASE WHEN status = 'active' THEN amount ELSE 0 END) as total
```

**Impact:** Data values change, which may affect downstream aggregations, reports, or ML models.

**Check:** Review business logic changes for unintended side effects.

## New Column with Default

**Risk: Low**

Adds a column with a default value.

**Impact:** Safe for most consumers, but may change `SELECT *` output.

## Column Order Change

**Risk: Low**

Reorders columns in a SELECT statement.

**Impact:** No effect on named columns, but `SELECT *` consumers may get different column order.
