# DataHub Root-Cause Analysis

Diagnose data incidents by tracing lineage to a **verifiable** root cause.

## What it does

1. Resolves the symptom (failing assertion / stale table / wrong dashboard)
2. Walks lineage upstream to a minimal suspect subgraph
3. Ranks candidate culprits from freshness, volume, schema, and query signals
4. Accepts a root cause **only** with a reconstructable lineage path + the
   transform SQL that carried the fault
5. Writes the incident dossier back to the catalog

## Capabilities

- **Path-grounded RCA** — no ungrounded diagnoses; every cause carries proof
- **Origin-seeking** — blames the upstream origin, not the intermediate victim
- **Cross-platform** — traces faults across Snowflake, dbt, Looker, etc.
- **Write-back** — persists a dossier + tags so the next person/agent inherits it

## Usage

```
/datahub-rca why did the revenue dashboard drop 40% this morning?
/datahub-rca root cause of the failing freshness assertion on daily_revenue
/datahub-rca diagnose this data incident: <urn>
```
