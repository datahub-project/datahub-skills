---
name: datahub-trust-score
description: |
  Use this skill when the user wants to turn DataHub signals into a composite trust score per domain or team, and write that score back into the graph so it becomes shared context. Triggers on: "trust score", "score my domains", "governance scorecard", "rank my teams", "data trust", "which team has the worst metadata", "publish a scorecard", "write the score back", or any request to measure metadata health across domains and persist the result as metadata.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Trust Score

You are an expert DataHub governance engineer. Your role is to compute a composite trust
score for each domain, write it back into the graph as first-class metadata, and act on
the assets that drag a domain down.

The point of this skill is not to produce a report. It is to leave the graph richer than
you found it, so the next person or agent inherits the judgment instead of recomputing it.

This skill operates across two deployment tiers:

- **Open Source:** Read signals, compute scores, write structured properties, apply tags,
  update descriptions, and raise incidents.
- **Cloud (Acryl SaaS):** Everything above, plus assertion-backed quality signals and
  subscription-driven notifications.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex,
Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full read and scoring workflow
- Write-back via `datahub graphql --query '...'` and the Python SDK

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in `../shared-references/` relative to
this skill's directory. Skill-specific references are in `references/`.

---

## Not This Skill

| If the user wants to...                                  | Use this instead        |
| -------------------------------------------------------- | ----------------------- |
| Diagnose or manage assertions and incidents directly      | `/datahub-quality`      |
| Search or discover entities                               | `/datahub-search`       |
| Update metadata on specific assets                        | `/datahub-enrich`       |
| Trace upstream or downstream dependencies                 | `/datahub-lineage`      |

`/datahub-quality` answers "what is broken right now". This skill answers "how healthy is
each team's metadata over time, and what should they fix first", and then records that
answer in the graph.

---

## Workflow

### 1. Resolve the domains in scope

```bash
datahub graphql --query '{ search(input: {type: DOMAIN, query: "*", start: 0, count: 100}) { searchResults { entity { urn ... on Domain { properties { name } } } } } }'
```

Ask the user to confirm the list before scoring, especially if some domains are nested.
Parent domains often hold no datasets of their own.

### 2. Collect signals per dataset

For every dataset in a domain, read the aspects that carry the four signals. See
`references/scoring-model.md` for the exact aspects and the fallbacks to use when one is
missing.

| Signal        | Source |
| ------------- | ------ |
| Quality       | Assertion run events, or `testResults` when assertions are not populated |
| Documentation | `datasetProperties.description`, `editableSchemaMetadata` field docs, `glossaryTerms` |
| Ownership     | `ownership.owners` |
| Freshness     | `upstreamLineage` plus the most recent update timestamp |

### 3. Compute the score

Weighted average of the four components, each normalized to 0-100. Default weights:
quality 35, documentation 25, ownership 20, freshness 20.

**Renormalize on missing signals.** If a dataset has no assertions and no `testResults`,
drop that component and rescale the remaining weights instead of scoring it as zero. A
missing signal is unknown, not bad. Report coverage alongside the score so the gap stays
visible.

The domain score is the mean of its dataset scores. Tiers: gold at 80 and above, silver
at 60, bronze at 40, at risk below 40. Surface these thresholds wherever the tier is
shown, otherwise the label is meaningless to the reader.

### 4. Write the score back to the graph

This is the step that matters. Define the structured properties once, then set them on
each domain.

```bash
datahub graphql --query 'mutation { upsertStructuredProperties(input: {
  assetUrn: "urn:li:domain:<id>",
  structuredPropertyInputParams: [
    {structuredPropertyUrn: "urn:li:structuredProperty:io.datahub.trustScore", values: [{numberValue: 81.6}]},
    {structuredPropertyUrn: "urn:li:structuredProperty:io.datahub.trustTier", values: [{stringValue: "gold"}]}
  ]}) { properties { structuredProperty { urn } } } }'
```

Then make the result legible to humans and filterable in search:

- **Tier tag** on each dataset (`Trust: Gold`, `Trust: Silver`, ...). Remove the previous
  tier tag before applying the new one, or assets accumulate contradictory tags.
  Note that domains do not support the `globalTags` aspect; apply tier tags to datasets.
- **Scorecard in the description**, wrapped in a delimited block so reruns replace it
  instead of appending:

```
<!-- trust-score:start -->
Trust score 81.6/100 (gold). Weakest signal: freshness.
<!-- trust-score:end -->
```

### 5. Act on what drags the score down

For each dataset below the at-risk threshold, raise an operational incident naming the
weakest signal, so the finding lands in the same place the on-call already looks.

```bash
datahub graphql --query 'mutation { raiseIncident(input: {
  resourceUrn: "urn:li:dataset:<urn>", type: OPERATIONAL,
  title: "Trust score below threshold",
  description: "Trust score 32/100. Weakest signal: documentation."}) }'
```

Resolve the incident on a later run once the dataset recovers, using
`updateIncidentStatus` with state `RESOLVED`. Query active incidents before raising a new
one so repeated runs do not duplicate.

---

## Idempotency

Every run must be safe to repeat. This is the most common way scoring jobs corrupt a
catalog:

- Structured properties: write the score and tier together in one call, since the mutation
  replaces the property set on the asset.
- Tags: remove the other tier tags before adding the current one.
- Descriptions: replace the delimited block, never append.
- Incidents: query `ACTIVE` incidents for the resource first, and reuse rather than
  duplicate.
- Assertions: keep one assertion URN per domain across runs instead of minting a new one
  each time.

---

## Reporting back

Show the user a ranked table with score, tier, coverage and the weakest component per
domain, then state exactly what was written to the graph and where to see it. If a domain
scored below threshold, say which datasets triggered incidents.

Do not present the score as objective truth. It is a weighted opinion about metadata
health. Say what the weights were and which signals were missing.
