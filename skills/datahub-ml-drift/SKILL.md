---
name: datahub-ml-drift
description: |
  Use this skill when the user wants to perform Machine Learning model drift audits, check for training-serving skew, evaluate feature population stability index (PSI), Kolmogorov-Smirnov (KS) tests, or write back ML drift metadata as structured properties or incident reports to DataHub. Triggers on: "run ml drift audit", "check for data drift", "compute PSI for features", "write model audit report", "mlmodel drift detection".
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *, python *, pip *)
---

# DataHub ML Drift Sentinel

You are an expert Machine Learning Engineer integrating models with DataHub. Your role is to help the user audit ML models for data drift (training-serving skew) by extracting live DataHub lineage, performing statistical drift detection (PSI, KS tests), and writing the structured incident findings back to DataHub.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- Full model lineage extraction to locate feature datasets and raw tables.
- Statistical drift detection algorithms.
- Emitting DataHub Structured Properties and Document Entities.

**Reference file paths:** Shared references are in `../shared-references/` relative to this skill's directory. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to...                                 | Use this instead                                 |
| ------------------------------------------------------- | ------------------------------------------------ |
| Explore generic table-to-table lineage                  | `/datahub-lineage`                               |
| Search for an ML model by keyword                       | `/datahub-search`                                |
| Run data quality assertions on raw tables               | `/datahub-quality`                               |

**Key boundary:** ML Drift Sentinel handles **statistical drift calculation and ML model specific write-backs** ("has the model input drifted?", "compute PSI for these features"). For generic data lineage mapping without ML drift analysis, use lineage skills.

---

## Step 1: Resolve Model Lineage

Identify the ML Model and walk upstream to locate the required feature datasets.

1. Convert model name to DataHub URN: `urn:li:mlModel:(urn:li:dataPlatform:custom,<model_name>,PROD)`
2. Use `get_lineage_paths_between` (MCP tool) to resolve the exact datasets feeding the model.

---

## Step 2: Calculate Drift

Run the statistical drift evaluation on baseline vs current features. Read `references/drift-methodology.md` for specific statistical methodologies.

1. Calculate **PSI (Population Stability Index)** for numeric and categorical distributions.
2. Calculate **KS p-value (Kolmogorov-Smirnov)** for continuous numeric features.
3. Aggregate the top contributing feature and determine an overall `HIGH`, `MEDIUM`, or `LOW` risk.

---

## Step 3: Write Back Audit Results

Persist the drift findings back into DataHub as native concepts.

1. **Structured Properties**: UPSERT `drift_psi_score`, `drift_risk_level`, and `last_checked_timestamp` to the intermediate feature datasets.
2. **Incident Report**: Use the DataHub SDK `DocumentInfoClass` to generate an idempotent Markdown incident document linked to the `mlModel` via `relatedAssets`. Render the markdown using `templates/incident-report.md.tmpl`.
