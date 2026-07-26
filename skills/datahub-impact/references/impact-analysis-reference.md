# Schema Change Impact Analysis Technical Reference

This document details technical specifications, lineage algorithms, scoring heuristics, remediation patterns, write-back mechanisms, and DataHub-specific architectural gotchas.

---

## 1. Lineage Traversal Algorithm: Column-Level + Dataset-Level Combined

When evaluating schema change impact, querying column-level lineage alone produces incomplete results because non-dataset entities (Looker dashboards, SageMaker ML models, Airflow DataJobs) connect to parent dataset URNs rather than individual `schemaField` URNs.

```text
Target Dataset (e.g. raw.customers) ───[Dataset Lineage]───> Looker Dashboard, ML Model, Airflow Job
      │
  schemaField (e.g. customer_id)  ───[Column Lineage]───> Downstream Dataset schemaFields
```

### Combined Traversal Procedure

1. **Dataset Lineage Fetch:** Query `get_lineage(urn="<dataset_urn>", upstream=False, max_hops=5)`.
2. **Column Lineage Fetch:** Query `get_lineage(urn="<schema_field_urn>", upstream=False, max_hops=5)`.
3. **Graph Filtering:**
   - Retain all non-dataset entities (`dashboard`, `mlModel`, `mlFeature`, `dataJob`, `dataFlow`) from dataset-level lineage.
   - Retain dataset entities (`dataset`) ONLY if their URN appears in the column-level lineage result.
   - Discard un-impacted sibling datasets.

---

## 2. 5-Factor Severity Heuristic Scoring

Each downstream asset is assigned a numerical score $S \in [0.0, 1.0]$:

$$S = \min\left(1.0, w_{\text{type}} + w_{\text{depth}} + w_{\text{usage}} + w_{\text{owner}} + w_{\text{env}}\right)$$

### Factor Weights

1. **Entity Type Weight ($w_{\text{type}}$):**
   - Dashboard / Chart: $+0.35$ (user-facing breakage)
   - ML Model / ML Feature: $+0.30$ (silent model degradation)
   - DataJob / DataFlow: $+0.25$ (pipeline execution failure)
   - Dataset: $+0.20$ (data propagation risk)
   - Other: $+0.15$
2. **Lineage Depth Weight ($w_{\text{depth}}$):**
   - Direct dependent (1 hop): $+0.30$ (immediate breakage)
   - 2 hops away: $+0.15$ (next refresh breakage)
   - 3+ hops away: $+0.05$ (buffered dependency)
3. **SQL Usage Weight ($w_{\text{usage}}$):**
   - JOIN key: $+0.25$
   - WHERE filter / GROUP BY: $+0.15$
   - SELECT reference: $+0.05$
   - None / Unknown: $+0.00$
4. **Ownership Signal Weight ($w_{\text{owner}}$):**
   - Assigned owner: $+0.05$ (actively maintained)
   - Unassigned: $+0.00$ (unmaintained risk)
5. **Environment Signal Weight ($w_{\text{env}}$):**
   - PROD environment: $+0.10$
   - DEV / STAGING: $+0.00$
   - Unknown environment: $+0.05$

### Severity Tiers

- **CRITICAL** ($S \ge 0.70$): Immediate production failure risk on core entities.
- **HIGH** ($S \ge 0.50$): Production pipeline, ML model, or key dataset impact.
- **MEDIUM** ($S \ge 0.30$): Secondary job or reporting dashboard impact.
- **LOW** ($S < 0.30$): Non-production or distant indirect dependency.

---

## 3. Change-Type Migration Guidance

### Rename (`rename`)

Transition strategy: Expose alias/view mapping -> Update downstream references -> Drop alias.

- Phase 1: Create SQL view mapping `old_col` to `new_col` on target table.
- Phase 2: Update dbt models, Looker views, and job queries to select `new_col`.
- Phase 3: Verify zero traffic to `old_col` and execute DROP.

### Drop (`drop`)

Deprecation sequence: Catalog deprecation -> Consumer decoupling -> DROP DDL.

- Phase 1: Mark column DEPRECATED in DataHub catalog; issue owner notifications.
- Phase 2: Remove column from SELECT lists, WHERE clauses, and ML feature extractors. Retrain ML models if features are removed.
- Phase 3: Execute `ALTER TABLE ... DROP COLUMN`.

### Type Change (`type_change`)

Boundary management: CAST wrapper -> Precision audit -> Dry-run test.

- Phase 1: Wrap downstream references in explicit `CAST(col AS <NEW_TYPE>)`.
- Phase 2: Audit narrowing conversions for numeric overflow or string truncation risks.
- Phase 3: Run test queries against sample data.

### Addition (`add`)

Non-breaking change (`ADD COLUMN`). No downstream migration steps required. Safe to merge.

---

## 4. Multi-Tier DataHub Write-Back Specifications

1. **MCP Insight Document:** Persist full Markdown report as a searchable Insight document via `save_document`.
   _Ordering Reason:_ `save_document` generates and returns the document URN (`summary["document_urn"]`). The document MUST be created first so subsequent structured properties can reference its URN in `breakingChange.reportUrn`.
2. **GraphQL Incidents:** Raise `DATA_SCHEMA` incidents on HIGH and CRITICAL assets via GMS GraphQL endpoint (`raiseIncident`).
3. **MCP Structured Properties:** Set `breakingChange.severity` and `breakingChange.reportUrn` (referencing the URN created in step 1) via `add_structured_properties`.
4. **MCP Tags:** Attach `urn:li:tag:BreakingChangeImpact` to all downstream assets via `add_tags`.

---

## 5. Architectural Gotchas

1. **MCP `search` Tool Omits ML Entities:** `search` skips `MLModel`, `MLFeature`, and `MLPrimaryKey` in GraphQL filters. Searching `tag:BreakingChangeImpact` fails to return ML assets. Use lineage graph traversal for cleanup.
2. **GraphQL Incident Type Restrictions:** Certain entities (e.g. `mlFeature`) reject `DATA_SCHEMA` incidents in DataHub GraphQL backend. Wrap incident creation calls in per-asset try/except blocks.
3. **Structured Property Prerequisites:** `breakingChange.severity` and `breakingChange.reportUrn` must be created via GraphQL `createStructuredProperty` before setting values.
4. **Tag Prerequisites:** Tags must exist in DataHub before `add_tags` can assign them.
5. **Absence of Fine-Grained Lineage:** Empty column-level lineage means lineage was not ingested, NOT zero impact. Always fall back to dataset-level lineage with explicit `Dataset-level inferred` labels.
6. **`mlFeature` Name Resolution:** `mlFeature` entities return the platform name in the `name` field on detail responses, so naive parsing renders every feature as its platform (for example, three distinct features all displaying as `sagemaker`). The feature's own name must be parsed from the first element of the URN tuple `(feature_name, platform_name)`.
7. **`dataJob` and `mlFeature` Platform Resolution:** For both entity types, `platform` is `None` on the entity detail response, producing `unknown`. For `dataJob`, the platform resolves from `dataFlow.platform.name` or `dataFlow.orchestrator`. For `mlFeature`, it resolves from the second element of the URN tuple.
