---
name: datahub-incident-response
description: |
  End-to-end data incident response over the DataHub metadata graph: detect anomalies,
  root-cause via lineage and query history, assess blast radius including ML deployments,
  propose fixes, and write back postmortems, tags, and incidents. Use when a dataset
  assertion fails, freshness SLA breaches, schema drift is suspected, null rates spike,
  or values look corrupted — especially when ML models or dashboards are downstream.
  Triggers on: "data incident", "investigate pipeline failure", "root cause for null spike",
  "blast radius", "hold ML deployment", "write postmortem to DataHub", "open DataHub incident",
  or any request to detect → diagnose → fix → document a data quality event.
user-invocable: true
allowed-tools: Bash(datahub *), Bash(curl *)
---

# DataHub Incident Response

Distilled from [Kavach](https://github.com/doPrashams/kavach) — a self-healing data platform
where LangGraph agents operate on DataHub's context graph.

## When to use

- A **DataHub assertion** or freshness check failed on a production dataset.
- **Lineage** suggests upstream schema drift, lagging ingestion, or corrupted source values.
- **ML models or deployments** consume the affected mart and may need a hold.
- You need a **postmortem Context Document**, incident record, and tags written back to DataHub.

## Prerequisites

1. DataHub CLI configured (`datahub init` or env vars). See `/datahub-setup`.
2. MCP Server reachable when using agent tools (`get_upstreams`, `create_incident`, etc.).
3. Agent Context Kit enabled for retrieve/write of Context Documents.

## Procedure (detect → root-cause → blast radius → fix → write-back)

### 1. Detect and confirm

1. Search for the failing dataset: `datahub get --urn "<dataset_urn>"`.
2. List open **incidents** and **assertions** on the entity.
3. Pull **query history** — recent queries often reveal the first broken transformation.
4. Confirm severity: compare null rates, freshness lag, or custom checks against SLOs.

**DataHub tools:** `search`, `get_dataset`, assertion entities, query history API/MCP.

### 2. Root-cause via lineage + queries

1. Walk **upstream lineage** (table + column level when available):
   - `get_upstreams(dataset, depth=2, column_level=true)`
2. Rank candidate causes: stale partition, renamed column, join drop, value corruption.
3. Retrieve **Context Documents** for similar past incidents:
   - `retrieve_context(entity_urn, query="prior postmortem <symptom>")`
4. If a prior postmortem matches, cite it and prefer the documented resolution.

**DataHub tools:** lineage traversal, Agent Context Kit retrieve, glossary/ownership lookup.

### 3. Blast radius (include ML)

1. Walk **downstream lineage** from the corrupted column or dataset.
2. Enumerate impacted dashboards, pipelines, and **ML entities**:
   - `dataset → mlFeature → mlModel → mlModelDeployment`
3. For each deployment at risk, record severity and recommend hold vs. monitor.

**DataHub tools:** `get_downstreams`, `get_blast_radius`, ML model/deployment entities.

### 4. Fix

1. Propose remediation: backfill, schema alias, null guard, range assertion.
2. Target the **demo pipeline repo** or your dbt/SQL project with a focused PR.
3. Add a **safeguard assertion** on the mart column that failed detection.
4. If ML risk is critical, recommend holding the deployment until the fix merges.

### 5. Write-back to DataHub

1. **Create incident** with affected entity URNs and root-cause summary.
2. **Save Context Document** postmortem (markdown) via Agent Context Kit.
3. **Add tags** (e.g. `incident-resolved`, scenario id) and update descriptions.
4. **Emit assertion** entity for the new safeguard test.
5. **Resolve incident** when validation passes.

**DataHub tools:** `create_incident`, `update_incident`, `resolve_incident`,
`save_context_document`, `add_tags`, `emit_assertion`.

## Reference paths in Kavach

| Artifact | Path |
|----------|------|
| Agent prompts | `backend/app/agents/prompts/` |
| DataHub service | `backend/app/datahub/service.py` |
| Chaos scenarios | `backend/app/chaos/scenarios/` |
| Example PRs | `examples/prs/` |
| Worked examples | `skills/datahub-incident-response/examples/` |

## MCP tool names (typical)

- `get_upstreams` / `get_downstreams` — lineage
- `get_dataset_queries` — query history
- `get_blast_radius` — downstream + ML impact
- `create_incident` / `resolve_incident` — incident lifecycle
- `save_context_document` — postmortem write-back
- `emit_assertion` — data quality entity
