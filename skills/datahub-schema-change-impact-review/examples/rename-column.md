# Example: Rename a Column

## Input

- Root: `urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.orders,PROD)`
- Column: `order_id`
- Change: rename
- New name: `purchase_id`

## Expected Workflow

1. Resolve the root and verify `order_id` in the real schema when available.
2. Retrieve real owners, tags, glossary terms, structured properties, and
   identifiable quality evidence.
3. Request downstream column lineage for `order_id`.
4. If the result is empty or unsupported, record fallback and request dataset
   lineage.
5. Deduplicate by URN, classify the returned assets, and calculate the fixed
   risk policy.
6. Generate rename SQL, a temporary compatibility view, tests, rollback steps,
   and a review summary. Do not execute the SQL.

## Example Output Shape

```text
Decision: <ALLOW | REVIEW | BLOCK from deterministic score>
Risk: <current score>/100
Unique downstream assets: <current DataHub count>
Approvals: <real normalized owner labels or none returned>
CLI trace: datahub get → datahub lineage (column downstream)
Fallback: <true with reason | false>
Safety: No migration SQL was executed.
```

Counts and metadata must come from the current DataHub response. Do not hardcode
this example's placeholders. Write-back, if requested, requires a new exact
preview and explicit human confirmation, and targets only the reviewed root
asset.
