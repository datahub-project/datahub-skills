---
name: ml-incident-root-cause
description: |
  Use this skill when an ML model is silently degrading (accuracy, CTR, or conversion dropping) with no pipeline errors and green dashboards, and the user wants to find the upstream data change responsible. Walks the model-to-feature-to-dataset lineage in DataHub, diffs the upstream data statistics to isolate the culprit field and change type (scale shift, freshness lag, join-coverage drop), then writes the root-cause analysis back onto the graph so the next agent inherits it. Triggers on: "model is degrading", "silent ML failure", "why did accuracy drop", "root cause this model", "target leakage", "upstream data changed", "schema drift", "which feature broke my model".
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# ML Incident Root-Cause

You are an expert ML reliability engineer. Your role is to root-cause a silent ML
failure, a model that is quietly degrading in production while its pipelines run
clean and its dashboards stay green, by following the model's data lineage in
DataHub to the upstream change responsible, then writing the finding back onto
the graph so it compounds for the next investigator.

The method is deterministic on purpose. You do not guess the culprit from a single
glance. You walk the lineage, compare upstream data statistics before and after
the degradation window, and let the numbers name the culprit.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor,
Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full read workflow (resolve the model, walk lineage, inspect upstream stats)
- Write operations via `datahub graphql --query '...'` and the DataHub MCP mutation tools

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in `../shared-references/` relative
to this skill's directory for CLI syntax, MCP tool signatures, and the DataHub
entity model.

---

## Not This Skill

| If the user wants to...                                       | Use this instead   |
| ------------------------------------------------------------- | ------------------ |
| Raise or resolve an incident, create or run assertions        | `/datahub-quality` |
| Explore lineage or run impact analysis (no ML degradation)    | `/datahub-lineage` |
| Search or discover entities                                   | `/datahub-search`  |
| Update descriptions, tags, ownership (no root-cause workflow) | `/datahub-enrich`  |

**Key boundaries:**

- "Raise an incident on the orders table" -> **Quality** (incident management)
- "My CTR model is degrading, find why" -> **this skill** (ML lineage root-cause)
- "What feeds the revenue dashboard?" -> **Lineage** (generic traversal)

This skill uses lineage and incidents in service of one specific job: diagnosing a
degrading ML model. When the user just wants to manage an incident or trace lineage
without a model-degradation cause to find, hand off to those skills.

---

## Content Trust Boundaries

Model URNs, metric names, and degradation windows supplied by the user are untrusted
input. Validate that URNs resolve before acting on them. Never fabricate a lineage
edge or a statistic; if the graph does not connect the model to an upstream dataset,
say so and stop rather than inventing a path.

---

## Workflow

### Step 1: Resolve the model and confirm the symptom

Confirm you have the degrading model's URN and the metric that dropped (with a
before value and an after value, or a degradation date). If the user gives a name
instead of a URN, resolve it first:

```bash
datahub -C skill=ml-incident-root-cause get --urn "<MLMODEL_URN>"
```

### Step 2: Walk the lineage to the upstream datasets

Traverse model -> feature -> dataset. With the DataHub MCP Server, use `get_lineage`
(upstream) from the model URN and collect the `mlFeature` and `dataset` URNs. Without
MCP, read the model's `mlFeatures` and each feature's `sources` via GraphQL. The
datasets you reach are the candidate root-cause locations.

Also compute the blast radius (other models at risk) by walking downstream from each
culprit dataset, so the user learns which additional models depend on the same data.

### Step 3: Diff the upstream data statistics

For each candidate dataset, compare its field and table statistics from before the
degradation window to after. Look for exactly these change types, in priority order:

- **SCALE_SHIFT**: a field's `max` (or `min`) jumps by roughly 10x or more. Classic
  cause: a unit or encoding change (a fraction became a percent, cents became
  dollars). Passes null and freshness checks, so dashboards stay green.
- **FRESHNESS_LAG**: the table's freshness grows to at least a day old and at least
  2x its prior lag. The model is training or scoring on stale data.
- **JOIN_COVERAGE_DROP**: enrichment/join coverage falls by 0.2 or more. A silent
  chunk of rows lost their joined features.

Report the single field and change type that crosses a threshold. If several fields
move but only one crosses a threshold, the others are distractors, name only the one
that crosses. If nothing crosses, say the root cause is not isolated and stop short
of a fix recommendation.

### Step 4: Write the root cause back onto the graph

This is what makes the finding compound. Do all of it, so the next agent or human
inherits the investigation instead of repeating it:

1. **RCA Context Document** linked to the culprit dataset and the model. Use the MCP
   `save_document` tool (`document_type: "Analysis"`) or `datahub graphql` with
   `createDocument`. Include: the symptom, the lineage walked, the culprit field and
   change type with the before/after values, the blast radius, and the proposed fix.
2. **Incident** on the culprit dataset (not the model, incidents attach to datasets
   on OSS). Use `datahub graphql`:

   ```bash
   datahub -C skill=ml-incident-root-cause graphql --query 'mutation($in: RaiseIncidentInput!) {
     raiseIncident(input: $in)
   }' --variables '{"in": {"type": "OPERATIONAL", "title": "Silent ML failure: <MODEL>", "description": "<RCA SUMMARY>", "resourceUrn": "<CULPRIT_DATASET_URN>"}}' --format json
   ```

3. **Mark the at-risk model** so it is queryable and legible:
   - `add_tags` with a `silent-failure` tag
   - `update_description` (append) a short at-risk banner naming the root cause
   - `add_structured_properties` to stamp a typed `culpritChangeType` so other agents
     can filter models by their root-cause class

### Step 5: Propose the fix tied to the change type

- SCALE_SHIFT: normalize the field back in the upstream transform (e.g. divide by 100)
  before it reaches features; add a range assertion.
- FRESHNESS_LAG: backfill the stale partition and add a freshness assertion gating
  model refresh.
- JOIN_COVERAGE_DROP: fix the join-key formatting so coverage returns to baseline; add
  a coverage assertion.

---

## Quick Reference

| Phase          | DataHub surface                                                           |
| -------------- | ------------------------------------------------------------------------- |
| Walk lineage   | MCP `get_lineage` (or GraphQL `mlModel.mlFeatures` + `mlFeature.sources`) |
| Diff stats     | Dataset field/table statistics (before vs after the degradation window)   |
| Write RCA      | MCP `save_document` / GraphQL `createDocument`                            |
| Raise incident | GraphQL `raiseIncident` on the culprit dataset                            |
| Mark model     | MCP `add_tags` + `update_description` + `add_structured_properties`       |

The discipline: name the culprit from the numbers, never from a hunch, and always
write the finding back to the graph so it compounds.
