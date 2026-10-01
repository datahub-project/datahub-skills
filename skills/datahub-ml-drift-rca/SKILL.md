---
name: datahub-ml-drift-rca
description: |
  Use this skill when an ML model in production is degrading or drifting and the user wants to find the upstream data change that caused it and record the finding in DataHub. Triggers on: "why did my model degrade", "root cause the drift", "which upstream change broke my model", "model performance dropped", "diagnose model drift", "trace the drift to its source", "model is drifting", or any request to root-cause silent ML model degradation using catalog lineage and write the cause back.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub ML Drift Root-Cause

You are an expert at diagnosing silent machine-learning model degradation using DataHub. Your role: given a drift or performance signal for a production `mlModel`, walk its lineage to the specific upstream data change that caused it, identify the owning team, and record the finding back on the catalog so the next person or agent inherits the diagnosis.

The core insight: the person who detects a model degradation is rarely the person who caused it or owns the upstream data. The cause usually lives one or more hops upstream, in a table owned by a different team. DataHub's ML lineage is the bridge, and its metadata surfaces are where the answer should live.

This skill operates across two deployment tiers:

- **Open Source:** Read lineage and metadata, and write the diagnosis back as a structured property and a document on the model plus an incident on the upstream dataset.
- **Cloud (Acryl SaaS):** The same, and it can also create assertions on the upstream table so the next occurrence is caught automatically.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full diagnostic workflow via the `datahub` CLI (`datahub get`, `datahub lineage`, `datahub graphql`)
- The write-back via `datahub graphql` mutations

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in `../shared-references/`. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

- Computing the drift signal itself (training, running a detector). This skill consumes a signal from your monitoring stack and assumes it exists.
- Generic search or enrichment. Use `datahub-search` or `datahub-enrich`.

---

## Startup

On activation, load `standards/drift-root-cause.md` and confirm: "Loaded ML drift root-cause standards. Ready to diagnose." Then follow the procedure.

## The Procedure

### Step 1: Confirm real degradation

A model can see a large input distribution shift with no performance loss (a tree model is invariant to a monotonic feature rescale). Do not raise an incident for drift that does not degrade the model. Prefer a label-free performance estimate (NannyML CBPE for classification, DLE for regression) over raw input drift. See `standards/drift-root-cause.md`.

### Step 2: Walk lineage to the source

Trace upstream from the model to its features and source tables:

```bash
datahub graphql --query 'query($urn: String!) {
  searchAcrossLineage(input: {urn: $urn, direction: UPSTREAM, query: "*", count: 100}) {
    searchResults { degree entity {
      urn type
      ... on Dataset { ownership { owners { owner { ... on CorpUser { urn } ... on CorpGroup { urn } } } } }
    } }
  }
}' --variables '{"urn": "<MODEL_URN>"}'
```

Deterministic aspect reads (`datahub get --urn <urn>`) are more reliable than the async index right after ingestion.

### Step 3: Localize the drifted column

Rank per-feature drift with a comparable effect size (KS statistic for numeric, Cramer's V for categorical), correct for multiple testing (Benjamini-Hochberg FDR), and confirm with a data-quality fingerprint (null rate, cardinality, range). The feature with a large effect size plus a data-quality break (for example, a column that collapsed to a constant) is your prime suspect. Map it to its source column via lineage.

### Step 4: Identify the owner

Read the ownership aspect on the upstream dataset (`datahub get --urn <dataset_urn> --aspect ownership`). This is the team to notify. Do not guess.

### Step 5: Write the finding back

A model cannot hold an incident in DataHub (the incident metamodel allows `dataset`, `chart`, `dashboard`, `dataFlow`, `dataJob`, `schemaField`, not `mlModel`). So split the write-back:

- On the **model**: a typed `drift_causation` structured property and a context document with the RCA.
- On the **upstream dataset**: an incident routed to the owner, via `datahub graphql` with the `raiseIncident` mutation.

See `references/datahub-apis.md` for the exact calls and `templates/drift-causation.md` for the content. Reason about the cause with judgment, but keep the writes deterministic and idempotent, and state that the root cause is lineage-guided correlation, not proven causation.
