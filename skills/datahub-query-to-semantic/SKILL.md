---
name: datahub-query-to-semantic
description: |
  Use when the user wants to mint dbt Semantic Layer metrics from institutional SQL,
  mine query history, compile semantic_models/metrics YAML from recurring patterns,
  or validate codegen against DataHub schema before write-back. Triggers on:
  "semantic layer from queries", "mint metrics from SQL history", "get_dataset_queries",
  "compile dbt metrics from production SQL", or "governed metrics from ad-hoc SQL".
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Query → Semantic Layer

You are an expert at turning **institutional SQL** (query history attached to datasets in DataHub)
into **validated dbt Semantic Layer artifacts** - never hallucinating column names.

Reference implementation: [QueryMint](https://github.com/HawaleShailesh004/querymint-app) (Apache-2.0).

---

## Not This Skill

| If the user wants to...     | Use instead                        |
| --------------------------- | ---------------------------------- |
| Ad-hoc NL → SQL chat        | Interactive SQL generation tools   |
| Schema PR migration testing | Schema change / migration workflows |
| Lineage impact only         | `/datahub-lineage`                 |

**Key boundary:** This skill **mines existing SQL** and **compiles batch artifacts** for git/CI -
not interactive chat SQL generation.

---

## Workflow

1. **Discover** - `search` datasets by business keyword (orders, revenue, etc.)
2. **Mine** - `get_dataset_queries(urn=<dataset>, count=50)` for institutional SQL
3. **Extract** - parse SELECT, GROUP BY, aggregations (sqlglot or structured parser)
4. **Cluster** - structural hash dedupe → recurring patterns
5. **Compile** - Jinja templates → `semantic_models/*.yml`, `metrics/*.yml`, staging SQL
6. **Validate (fail-closed)** - every column ref must exist in `list_schema_fields`; reject unknowns
7. **Write-back** (only if validation passed):
   - `save_document` with YAML + representative SQL
   - Append `[QueryMint]` to description
   - Tag `semantic-layer-candidate`
   - Use PENDING → read-back → VERIFIED protocol before marking complete

---

## MCP tools

| Tool                  | Role                                  |
| --------------------- | ------------------------------------- |
| `search`              | Find target datasets                  |
| `get_dataset_queries` | **Primary input** - institutional SQL |
| Schema / entity read  | Column allow-list for validation      |
| `save_document`       | Attach compiled spec                  |
| Tags / description    | Surface metrics for next agent        |

---

## Fail-closed rule

**Never emit YAML with column names not confirmed in catalog schema.** Prefer refusing over hallucinating.

Run `dbt parse` on compiled artifacts when dbt is available before proposing a PR.

---

## Reference documents

| Document                           | Purpose                                       |
| ---------------------------------- | --------------------------------------------- |
| `references/workflow-reference.md` | Step-by-step with CLI equivalents             |
| QueryMint repo `examples/`         | Sealed demo bundle (16 queries → 10 clusters) |

---

## Remember

- Query history is the source of truth for **what the org actually measures**
- Schema metadata is the source of truth for **which columns exist**
- Write-back closes the loop so the **next agent inherits official definitions**
