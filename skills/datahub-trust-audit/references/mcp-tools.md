# MCP tools — datahub-trust-audit engine

The engine runs as an MCP server: `python -m trust_layer.mcp_server` (stdio). Register it in
your agent's MCP config alongside the official DataHub MCP server. Tools it exposes:

## `audit_dataset(dataset_urn: str, write_back: bool = True) -> str`

Auto-fed audit. Reads the train/test split SQL from DataHub query history for `dataset_urn`,
classifies the methodology, runs the honest-metrics checks, and (default) writes the verdict
back as Assertion + Incident + Tags. Returns the rendered verdict card.

## `classify_split_sql(sql: str) -> str`

Stateless lint of a single split query → `TEMPORAL` (clean), `RANDOM` (leakage risk), or
`UNKNOWN`. Use for a quick check before a full audit, or in CI on a training pipeline's SQL.

## `list_auditor_skills() -> str`

Lists the honest-metrics checks (temporal leakage, overfit, calibration) with what each catches.

## Companion: the official DataHub MCP server

This skill READS via the official `mcp-server-datahub` tools (`search`, `get_lineage`,
`get_dataset_queries`, `list_schema_fields`, `get_entities`) and WRITES via its own emitter
(assertions/incidents/tags). Enable mutations with `TOOLS_IS_MUTATION_ENABLED=true` if you
prefer the DataHub server to apply tags.

## CLI equivalents (no MCP client required)

```bash
trust-layer selftest                 # prove the statistical core with no DataHub
python scripts/audit_auto.py <urn>   # auto-fed audit + write-back
python scripts/sentinel_scan.py      # source data-health scan (drift/null/schema)
```
