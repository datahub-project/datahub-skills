# Workflow reference - query to semantic layer

## CLI equivalents (QueryMint)

```bash
# Offline demo (no Docker)
pip install -e ".[dev]"
querymint demo && querymint verify

# Show mined SQL (video / live proof)
querymint mine --no-fixture

# Full pipeline + write-back
querymint run --write-back --no-fixture
```

## Validation gates

1. **Schema gate** - all `expr:` refs in YAML/SQL ∈ catalog columns
2. **dbt parse** - `dbt parse` in ephemeral project (when dbt installed)
3. **Write-back protocol** - PENDING → read-back → VERIFIED

## Example outcome

- 16 institutional queries mined
- 10 structural clusters
- 10/10 artifacts passed validation
- Eval: **18/18** grounded column picks vs **0/18** ungrounded baseline (pipeline-derived, orders + customers)
