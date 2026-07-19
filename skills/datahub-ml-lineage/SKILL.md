---
name: datahub-ml-lineage
description: |
  Use this skill when the user wants to audit or protect a production ML model using DataHub's ML lineage graph (training data -> features -> models -> deployments), investigate target leakage, trace what breaks if an upstream table changes, or figure out why a model's accuracy dropped. Triggers on: "is this model at risk of leakage", "audit this model's lineage", "what breaks if I change this table", "why did this model's accuracy drop", "does this model need a retrain", "trace ML lineage for X", or any request involving MLModel/MLFeature/MLFeatureTable/MLModelDeployment entities.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub ML Lineage

Use this skill when asked to investigate, audit, or protect a production ML
model using DataHub -- e.g. "is this model at risk of leakage", "what breaks
if I change this table", "why did this model's accuracy drop", or "does
`<model>` need a retrain". It complements the core `lineage` skill (which
covers general dataset lineage) with patterns specific to the ML entity
chain: `MLFeatureTable -> MLFeature -> MLModel -> MLModelGroup ->
MLModelDeployment`.

This skill assumes MCP tool access to a DataHub instance (`get_lineage`,
`get_entities`, `search`, and, for write-back, `add_tags` / `save_document` /
`update_description`).

## Core workflow

1. **Resolve the model.** Use `search` with `filter: 'type:MLMODEL'` (or a
   name query) to find the model's URN. Confirm with `get_entities`.

2. **Pull the full upstream graph in one call.** Don't fetch features one at
   a time -- call `get_lineage` once, upstream, with a generous `max_hops`
   (5-6 typically reaches raw source tables through a feature mart):

   ```
   get_lineage(urn=<model_urn>, upstream=true, max_hops=6, max_results=50)
   ```

   The result's `upstreams.searchResults[]` contains every `MLFeature` and
   `Dataset` in the model's dependency graph, each with its own
   `properties.customProperties`, `glossaryTerms`, `tags`, and `ownership`
   already attached -- no need for a second round-trip per entity in the
   common case. See `references/lineage-shapes.md` for the exact response
   shape and field paths.

3. **Check for leakage risk -- and discover it, don't just read it.** Look
   for glossary terms or tags on upstream datasets that signal "this data
   reflects the outcome, not a predictor of it" -- e.g. a term like
   `PostOutcomeEvent`. If your DataHub instance doesn't yet have such a term,
   propose creating one (see `templates/leakage-glossary-term.md`) rather
   than inventing an ad hoc tag per project -- a shared term lets every
   future audit reuse the same signal.

   The stronger version of this step: don't wait for someone to have
   pre-tagged the risky tables. Run a **semantic triage pass** first --
   `search(query="*", filter="entity_type = dataset")` for every dataset not
   already carrying the term, read its real `properties.description` via
   `get_entities`, and ask an LLM to judge from that prose alone whether the
   data is causally downstream of a business outcome (a refund filed because
   someone is leaving, a survey completed because a subscription was
   cancelled). If so, attach the term yourself with `add_terms`. This turns
   "check if someone already flagged it" into "flag it if nobody has,"
   and it composes: once one audit tags an upstream table, every other
   model sharing that table benefits without re-deriving the judgment.
   Validate this kind of classifier against known-clean data too (ordinary
   reference/dimension tables) -- a detector that flags everything is as
   useless as one that flags nothing.

4. **Check for blast radius / staleness.** Compare `lastModified` /
   freshness signals (or `customProperties` freshness fields, or DataHub
   Cloud assertions where available) across sibling tables in the same
   schema/container. A common real-world pattern: an upstream table is
   renamed or replaced, the old table goes quiet, but nothing downstream was
   ever repointed. If two datasets in the same container have very
   different last-observed timestamps and one appears in a feature's
   lineage while the other doesn't, that is the smoking gun.

5. **Write findings back, don't just print them.** The point of using
   DataHub for this instead of a one-off script is that the _next_ agent or
   engineer inherits your findings:
   - `add_tags` the model and deployment (e.g. `model-at-risk`,
     `leakage-suspect`) so it surfaces in search/dashboards.
   - `save_document` (type `Analysis`) with the evidence chain, linked via
     `related_assets` to every entity involved. Note: `relatedAssets` does
     **not** accept `mlModelDeployment` URNs as of DataHub 1.x -- link the
     `MLModel`, `Dataset`, and `MLFeature` URNs instead.
   - `update_description` (operation `append`) with a one-line pointer to
     the Analysis document, so anyone viewing the model in the DataHub UI
     sees the finding immediately, not just people who know to search for
     it. Guard against duplicate appends across repeated runs by checking
     the current description for a stable marker string first.

6. **Generate the fix, not just the flag.** If you have repo access to the
   pipeline that produced the offending feature (dbt models, feature
   pipeline code), propose the actual diff -- removing the leaking column,
   or repointing a `ref()`/source to the correct upstream table -- rather
   than stopping at "someone should look into this." See
   `templates/remediation-pr.md`.

## Common pitfalls

- **Don't assume `get_entities` on an `MLModel` or `MLFeature` returns
  `mlFeatures` / `sources`.** The MCP server's entity-details fragment
  intentionally keeps ML entity payloads light (name, description,
  ownership, tags, glossary terms) -- it does not project
  `MLModelProperties.mlFeatures` or `MLFeatureProperties.sources`. Get that
  structure from `get_lineage` instead, which walks the graph edges
  directly.
- **`get_lineage` strips `paths` for entity-level (non-column) lineage** to
  keep responses small, so you can't attribute "this exact feature comes
  from this exact upstream table" purely from the response -- you get the
  full upstream _set_, not per-edge attribution. For most audits the set is
  enough; if you need edge-level attribution, fall back to column-level
  lineage (`get_lineage(..., column=<field>)`) or inspect
  `MLFeatureProperties.sources` via a raw GraphQL/REST call.
- **Tags and glossary terms must exist before you can apply them.** If
  `add_tags`/`add_terms` fails with "Urn does not exist", the tag/term
  entity itself needs to be created first (via ingestion or the DataHub UI)
  -- MCP mutation tools apply labels, they don't invent the taxonomy.
  `mcp-server-datahub` has no `create_glossary_term` tool, only attachment.
- **`search`'s `filter` argument uses `field = value` syntax, not
  `field:value`.** `filter="entity_type = dataset"` works;
  `filter="_entityType:DATASET"` raises a parse error ("Expected =, !=, >,
  ... after field name"). The tool's own docstring documents this but it's
  easy to guess wrong from familiarity with DataHub's `/q` search syntax,
  which uses a different grammar for a different parameter.
- **`get_entities` is heavier than it looks.** Beyond the requested entity
  fields, it also fetches `relatedDocuments` and, for some entity types, a
  lineage-adjacent query -- each call can be 2-3 GraphQL round-trips, not
  one. Calling it twice per entity (once to check existing state, once for
  detail) roughly doubles an audit's wall-clock time for no reason; fetch
  once and reuse the result.

## References

- `references/lineage-shapes.md` -- exact JSON shapes returned by
  `get_lineage` and `get_entities` for ML entity types, with field paths.
- `templates/leakage-glossary-term.md` -- proposed definition for a reusable
  `PostOutcomeEvent`-style glossary term.
- `templates/remediation-pr.md` -- structure for a generated remediation PR
  description that references DataHub evidence.
