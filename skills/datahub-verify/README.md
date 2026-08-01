# datahub-verify

Evidence-first verification for DataHub-backed agents. It checks proposed data-code changes, compares catalog context with live sources, and keeps unverified or stale assets distinct from verified ones.

## What it does

- Calls `check_change` before an agent proposes SQL and honors `BLOCK` decisions.
- Calls `verify_context(urn)` before trusting an asset's catalog metadata.
- Uses `search_verified` for broad selection and preserves freshness and abstention states.
- Explains deterministic versus advisory findings and reproducible, expiring receipts.

## Usage

```
> Verify this SQL before proposing it
> Is this DataHub dataset trustworthy right now?
> Find verified customer assets for a broad query
```

## Files

| File       | Purpose                                 |
| ---------- | --------------------------------------- |
| `SKILL.md` | Main verification workflow and examples |
