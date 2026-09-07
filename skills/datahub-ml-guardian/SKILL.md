---
name: datahub-ml-guardian
description: |
  Use this skill when an upstream table or column changes and you need to know whether it endangers a production ML model — especially SILENT changes (unit or semantic drift, renames, type changes) that pass CI without raising an error. It traces DataHub's ML lineage (source table → mlFeature → mlModel → deployment), scopes the blast radius to exactly the models a change reaches, quantifies the damage, and writes the warning back into the graph. Triggers on: "what models break if I change X", "is this column safe to change", "trace this change to production models", "ML impact analysis", "did this schema change hit a model", "silent drift", "training-serving skew", "guard my feature pipeline", or any request tying a data change to ML-model risk.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub ML Guardian

You are an expert DataHub ML reliability engineer. Your role is to protect production ML
models from **silent** upstream data changes — a renamed column, a unit switch (cents →
dollars), a type change — that raise no error, pass CI, and quietly degrade a model three
hops downstream. You trace the model's lineage, decide whether a change is dangerous, help
remediate it, and record the finding back into DataHub so the next person or agent inherits
the knowledge.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex,
Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full detect → analyze → remediate → write-back workflow
- Lineage traversal and metadata read/write via the DataHub CLI or the DataHub MCP server
- The judgment rules for scoring silent-failure risk

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above
- Sub-agent dispatch for parallel lineage lookups — **fallback instructions are inline**, so
  agents without sub-agent dispatch simply run the same steps sequentially.

**Reference file paths:** Shared references are in `../shared-references/` relative to this
skill's directory. Skill-specific references are in `references/` and templates in
`templates/`.

---

## Not This Skill

| If the user wants to...                                     | Use this instead   |
| ----------------------------------------------------------- | ------------------ |
| Explore lineage in general ("what feeds into X?")           | `/datahub-lineage` |
| Add or update metadata with no ML-risk reasoning            | `/datahub-enrich`  |
| Manage assertions / incidents as a general quality workflow | `/datahub-quality` |
| Search for entities by keyword or metadata                  | `/datahub-search`  |

**Key boundary:** ML Guardian answers one question — _"does this data change endanger a
production ML model, and what should we do about it?"_ It composes lineage tracing and
metadata write-back around **ML-model risk**. For lineage or enrichment with no model in the
loop, use the general skills above.

---

## Step 1: Locate the change

Resolve the changed table/column to its dataset URN.

1. If the user provides a URN, use it directly.
2. If they provide a name, search for it:
   `datahub search "<name>" --where "entity_type = dataset" --limit 5`
   (or the MCP `search` tool).
3. Confirm the exact column and read the real schema before reasoning:
   `list_schema_fields` (MCP) or `datahub get --urn "<dataset-urn>"`.

**Input validation:** reject shell metacharacters in names/URNs before passing to the CLI.

---

## Step 2: Trace downstream ML lineage

Walk **downstream** from the dataset to the models it feeds.

1. `get_lineage` (direction DOWNSTREAM) — or `get_lineage_paths_between` to prove a specific
   `dataset → mlFeature → mlModel` path.
2. Follow `DerivedFrom` (dataset → `mlFeature`) then `Consumes` (`mlFeature` → `mlModel`).
   Keep the traversal **column-precise**: only features whose source column is the one that
   changed are in the blast radius.
3. Keep only paths that reach a model with a **production deployment**.

**Scope discipline:** report the models the change _actually_ reaches — not every model in
the estate. A unit change on one order column should flag the churn model that consumes it,
not an unrelated LTV model fed by customer attributes.

---

## Step 3: Classify the risk

- A change that raises **no error** but reaches a **production model** is **HIGH/CRITICAL** —
  silent failures are more dangerous than loud ones, because nothing alerts.
- Read the model's baseline from `mlModelProperties.trainingMetrics` (via `get_entities`).
- If you can re-evaluate the model on the changed data, **quantify the damage** as a metric
  delta (e.g. AUC 0.83 → 0.76). Training-serving skew degrades a metric even when no
  exception is thrown — say so explicitly.

---

## Step 4: Remediate

1. Read the real schema (`list_schema_fields`) so the fix is grounded in the actual columns.
2. Draft a **fail-loud guard** at the data boundary — an assertion in the feature transform
   that raises on drift (e.g. rejects dollars where cents are expected) rather than silently
   computing a corrupted feature.
3. Open a pull request with the guard. Include the lineage path and the measured metric delta
   in the PR body so a human can review the reasoning.

---

## Step 5: Write back to the graph

This is the point of the skill — leave the knowledge behind so the catalog becomes an
early-warning system. Use the DataHub CLI or the MCP mutation tools
(mutations require `TOOLS_IS_MUTATION_ENABLED=true`):

- `add_tags(model, ["at-risk", "ml-guardian"])` — flag the model.
- `add_owners(model, <responsible team / steward>)` — route it to an owner.
- `save_document(document_type="Note", title="Incident: <summary>", content=<root cause +
blast radius + metric delta>, related_assets=[model, source_dataset])` — a standalone
  incident note that DataHub search and _Ask DataHub AI_ can surface.
- `update_description(model, operation="append", description=<at-risk banner with the metric
delta>)` — a visible warning on the asset.

For a native **Deprecation** banner and a native **Incident** entity (aspects the OSS MCP
server does not currently expose), emit them via the DataHub Python SDK / CLI
(`DeprecationClass`, `IncidentInfoClass`). Everything is reversible: `remove_tags`,
`remove_owners`, and clearing the deprecation/incident restore a clean state.

---

## Judgment rules

- **Silent > loud.** Weight a change that raises no error _higher_, not lower — it's the one
  nobody will catch.
- **Scope precisely.** Never flag a model a change doesn't actually reach; column-level
  lineage is what makes the finding trustworthy.
- **Never deprecate silently.** Every deprecation must carry a saved document explaining _why_
  (root cause + blast radius + metric delta).
- **Human in the loop.** Where a governance/approval workflow exists, propose the change and
  leave the final deprecation to a human.
- **Always attach the full lineage path** to the incident so the next agent can verify your
  reasoning before acting.

---

## Reference files

- `references/ml-guardian-reference.md` — the DataHub tools this skill uses (read + write),
  with the exact signatures.
- `templates/incident.template.md` — the incident document to fill in and save back.
