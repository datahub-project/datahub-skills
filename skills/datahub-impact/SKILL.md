---
name: datahub-impact
description: |
  Use this skill when the user wants to analyze the blast radius of a proposed database schema change (column rename, field drop, type change, or column addition), trace column and dataset lineage, rank downstream assets by severity, generate a remediation migration plan, or write impact markers back into DataHub. Triggers on: "schema change impact", "blast radius", "what breaks if I rename X", "drop column impact", "type change blast radius", "impact analysis for column X", "migration plan for schema change".
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Schema Change Blast Radius Analysis

You are an expert DataHub schema change analyst. Your role is to help users assess the blast radius of proposed database schema changes (column renames, field drops, type alterations, and column additions) across downstream data pipelines, dashboards, ML models, and metrics, generating actionable remediation migration plans and writing impact state back into DataHub.

---

## Multi-Agent Compatibility

This skill works across AI coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- Full 7-step schema change impact analysis procedure
- Combined column-level and dataset-level lineage traversal
- 5-factor severity heuristic scoring and tier classification
- Remediation migration plan generation with change-type-specific checklists
- Multi-tier write-back using MCP tools and DataHub GraphQL API

---

## Skill Boundaries (Not This Skill)

| If the user wants to...                                   | Use this skill instead |
| --------------------------------------------------------- | ---------------------- |
| Search or discover entities by keyword                    | `/datahub-search`      |
| Add or update basic metadata (descriptions, tags, owners) | `/datahub-enrich`      |
| Explore general data lineage ("what feeds into X")        | `/datahub-lineage`     |
| Manage assertions and data quality checks                 | `/datahub-quality`     |
| Set up connection or configure profiles                   | `/datahub-setup`       |

**Key Boundary:** Use `/datahub-impact` specifically when analyzing a **proposed schema change** (table/column + change type) to quantify downstream breakage, rank assets by severity, create migration checklists, and write impact metadata back into DataHub.

---

## Procedure: 7 Steps for Schema Change Impact Analysis

### Step 1: Establish Target Entity and Column URNs

Identify the dataset and column targeted for the schema change.

1. **Resolve Dataset URN:** Search for the dataset by name using `search(query="<dataset_name>")` or `datahub search "<dataset_name>" --where "entity_type = dataset"`.
2. **Dataset URN Format:** `urn:li:dataset:(urn:li:dataPlatform:<platform>,<dataset_name>,<env>)`
3. **Construct SchemaField URN:** If a column is specified, construct the column-level URN:
   `urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:<platform>,<dataset_name>,<env>),<column_name>)`
4. **Verify Schema:** Call `list_schema_fields(urn="<dataset_urn>")` to confirm the targeted column exists in the schema.

---

### Step 2: Combined Column-Level and Dataset-Level Lineage Tracing

To capture complete blast radius accurately, combine column-level and dataset-level lineage tracing.

> [!IMPORTANT]
> **Lineage Traversal Rule:** Column-level lineage (`schemaField`) traces field-to-field mappings between datasets, but omits non-dataset assets like Looker dashboards (`dashboard`), ML models (`mlModel`), ML features (`mlFeature`), and Airflow jobs (`dataJob`), because those entities attach to parent datasets rather than individual columns.

**Combined Traversal Algorithm:**

1. **Fetch Dataset-Level Lineage:** Execute `get_lineage(urn="<dataset_urn>", upstream=False, max_hops=5)` to retrieve all downstream dependents (datasets, dashboards, ML models, jobs).
2. **Fetch Column-Level Lineage:** If a column name is specified, execute `get_lineage(urn="<schema_field_urn>", upstream=False, max_hops=5)`.
3. **Extract Impacted Datasets:** Collect dataset URNs returned by the column-level lineage trace.
4. **Prune Dataset Graph:**
   - Keep non-dataset assets (dashboards, ML models, jobs) returned by dataset-level lineage.
   - Keep dataset assets ONLY if they appear in the column-level lineage trace.
   - Filter out unaffected sibling datasets.

---

### Step 3: Label Lineage Confidence Honestly

Transparency regarding lineage confidence is mandatory:

- **Column-Level Confirmed:** Assets reachable through verified column-level lineage edges are labeled `Column-level confirmed`.
- **Dataset-Level Inferred:** Assets reachable only through dataset-level lineage (or when fine-grained column lineage was omitted during ingestion) are labeled `Dataset-level inferred (column-level lineage unavailable)`.

> [!WARNING]
> **Silence Is Not Safety:** When column-level lineage returns 0 edges, it indicates that fine-grained lineage was not emitted for that table—NOT that zero assets are impacted. Fall back to dataset-level lineage and explicitly label output as `Dataset-level inferred`. Never present inferred impact as confirmed.

---

### Step 4: Enrich Downstream Assets and Analyze Query Usage

For each impacted asset identified in Step 2:

1. **Batch Metadata Enrichment:** Call `get_entities(urns=[...])` in a single batched call to retrieve ownership (`ownership`), platform (`platform`), environment, and descriptions.
2. **Query Usage Inspection:** Call `get_dataset_queries(urn="<dataset_urn>")` to check how the column is referenced in real SQL statements:
   - `JOIN` key (structural dependency)
   - `WHERE` clause (filtering logic)
   - `GROUP BY` clause (aggregation logic)
   - `SELECT` clause (output schema projection)

---

### Step 5: Rank Severity Using 5-Factor Heuristic

Compute a severity score ($0.0 \le \text{Score} \le 1.0$) for each downstream asset based on five structural factors:

| Factor                    | Criteria                            | Weight / Points                 |
| ------------------------- | ----------------------------------- | ------------------------------- |
| **1. Entity Type**        | Dashboard / Chart                   | +0.35                           |
|                           | ML Model / ML Feature               | +0.30                           |
|                           | DataJob / Pipeline                  | +0.25                           |
|                           | Dataset                             | +0.20                           |
| **2. Lineage Depth**      | Direct dependent (1 hop)            | +0.30                           |
|                           | 2 hops away                         | +0.15                           |
|                           | 3+ hops away                        | +0.05                           |
| **3. SQL Usage**          | JOIN key                            | +0.25                           |
|                           | WHERE filter / GROUP BY aggregation | +0.15                           |
|                           | SELECT projection                   | +0.05                           |
| **4. Ownership Signal**   | Owner assigned                      | +0.05                           |
|                           | No owner assigned                   | +0.00 (flagged as unmaintained) |
| **5. Environment Signal** | PROD environment                    | +0.10                           |
|                           | DEV / STAGING environment           | +0.00                           |
|                           | Unknown environment                 | +0.05                           |

**Severity Tier Thresholds:**

- **CRITICAL** ($\text{Score} \ge 0.70$): Direct production breakage or high-visibility consumer impact.
- **HIGH** ($\text{Score} \ge 0.50$): High-risk downstream pipeline or model dependency.
- **MEDIUM** ($\text{Score} \ge 0.30$): Secondary reporting or batch job dependency.
- **LOW** ($\text{Score} < 0.30$): Indirect or non-production asset.

---

### Step 6: Generate Remediation Migration Plan

Construct a structured remediation plan tailored to the specific change type (`rename`, `drop`, `type_change`, `add`):

#### Change-Type Specific Transition Strategies

- **`rename` (Column Rename):**
  1. _Phase 1 (Add Alias):_ Expose a view or alias mapping `old_column` to `new_column` on the target table during a transition window (e.g. 48h).
  2. _Phase 2 (Migrate Consumers):_ Update downstream dbt models, queries, and dashboards to select `new_column`.
  3. _Phase 3 (Cleanup):_ Drop transition alias after all consumers confirm migration.
- **`drop` (Column Drop):**
  1. _Phase 1 (Deprecate):_ Mark column as DEPRECATED in DataHub catalog and notify assigned owners.
  2. _Phase 2 (Decouple):_ Remove column references from SQL views, job scripts, and ML feature extractors. Explicitly flag if ML model retraining is required.
  3. _Phase 3 (Drop DDL):_ Execute `ALTER TABLE ... DROP COLUMN` after deprecation grace period.
- **`type_change` (Type Modification):**
  1. _Validate Boundary:_ Implement explicit `CAST(column AS <NEW_TYPE>)` in downstream view models.
  2. _Precision Audit:_ Audit narrowing conversions for numeric truncation or overflow risk.
  3. _Dry-Run Test:_ Execute verification queries against sample data before altering storage DDL.
- **`add` (Column Addition):**
  1. State plainly that column additions are non-breaking (`ADD COLUMN`). No consumer migration steps required. Safe to merge.

#### Owner-Grouped Remediation Checklist

Group remediation items by asset owner (highest severity assets first), providing:

- Asset URN, entity type, platform, and severity tier
- Specific fix required (e.g., update SQL projection, adjust JOIN key, retrain ML model)
- Confidence tag: `high confidence` (column-level confirmed) or `verify manually` (dataset-level inferred or missing query context)

---

### Step 7: Write Impact Metadata Back to DataHub

Persist analysis results back into DataHub to inform team members and downstream agents:

1. **Persist Insight Document (MCP Tool):**
   Call `save_document` with `document_type="Insight"`, title `Impact Report: <change_details>`, markdown content, and related asset URNs.
   _Ordering Reason:_ `save_document` generates and returns the document URN (`summary["document_urn"]`). The document MUST exist first so subsequent steps can reference its URN.
2. **Raise GraphQL Incidents (HIGH & CRITICAL Assets):**
   Use DataHub GraphQL API `raiseIncident` mutation to open `DATA_SCHEMA` incidents on HIGH and CRITICAL assets for active alerting.
   _Note:_ Incidents require GraphQL GMS endpoint (`/api/graphql`) as they are not exposed in stock MCP toolsets.
3. **Apply Structured Properties (MCP Tool):**
   Call `add_structured_properties` to attach `breakingChange.severity` (e.g., `HIGH`) and `breakingChange.reportUrn` (referencing the document URN created in step 1) to all impacted assets.
   _Prerequisite:_ Structured properties must be pre-created in DataHub catalog.
4. **Tag Impacted Assets (MCP Tool):**
   Call `add_tags` to attach `urn:li:tag:BreakingChangeImpact` to all downstream assets.
   _Prerequisite:_ Tag definition must exist in DataHub catalog.

---

## Crucial DataHub Architectural Gotchas

These hard-won implementation details ensure reliable interaction with DataHub:

1. **MCP `search` Tool Omits ML Entities:** The MCP `search` tool's underlying GraphQL query filters out ML entities (`MLModel`, `MLFeature`, `MLPrimaryKey`). Searching `tag:BreakingChangeImpact` via `search` will NOT return tagged ML assets. Always use lineage traversal context (`get_lineage`) for complete cleanup.
2. **GraphQL Incident Type Constraints:** Certain entity types (such as `mlFeature`) do not support `DATA_SCHEMA` incidents in DataHub GMS backend and return mutation errors. Always wrap incident creation calls per-entity in try/except blocks to prevent single-asset failures from aborting write-back.
3. **Structured Properties Pre-definition:** Structured properties (`breakingChange.severity`, `breakingChange.reportUrn`) must be registered as entities via `createStructuredProperty` GraphQL mutation before `add_structured_properties` can set values on assets.
4. **Tag Pre-creation:** Tags (e.g. `urn:li:tag:BreakingChangeImpact`) must exist in the DataHub catalog before `add_tags` can apply them to entities.
5. **Absence of Column Lineage Means Unknown:** If fine-grained column lineage was omitted during metadata ingestion, column-level lineage queries return empty lists. Silence indicates "lineage unavailable", NOT "zero impact". Always fall back to dataset-level lineage with clear `Dataset-level inferred` confidence labeling.
6. **`mlFeature` Name Resolution:** `mlFeature` entities return the platform name in the `name` field on detail responses, so naive parsing renders every feature as its platform (for example, three distinct features all displaying as `sagemaker`). The feature's own name must be parsed from the first element of the URN tuple `(feature_name, platform_name)`.
7. **`dataJob` and `mlFeature` Platform Resolution:** For both entity types, `platform` is `None` on the entity detail response, producing `unknown`. For `dataJob`, the platform resolves from `dataFlow.platform.name` or `dataFlow.orchestrator`. For `mlFeature`, it resolves from the second element of the URN tuple.

---

## CLI Command Attribution

When running CLI commands during analysis, pass `-C skill=datahub-impact`:

```bash
datahub -C skill=datahub-impact search "raw_customers"
datahub -C skill=datahub-impact lineage --urn "urn:li:dataset:(urn:li:dataPlatform:postgres,raw.customers,PROD)" --direction downstream
```

---

## Reference Implementation

For a complete working Python reference implementation, CLI tool, and GitHub Action CI/CD integration, see [IshekKhal/breaking-change-radar](https://github.com/IshekKhal/breaking-change-radar).
