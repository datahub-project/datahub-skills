---
name: datahub-demand
description: |
  Use this skill when a search of the DataHub catalog returns nothing and the agent or user needs to know whether the asset is genuinely absent or merely unfound, and to record the unmet need so it is not discarded. Triggers on: "there is no table for X", "I could not find X in the catalog", "does X exist?", "nothing matched", "we need a dataset for X", "record this as a gap", or any point where an agent is about to conclude that data does not exist. For finding assets that do exist, use `/datahub-search`. For adding metadata to an asset that exists, use `/datahub-enrich`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Demand

You establish whether an asset the user or an agent needs is **genuinely absent** from the
catalog, and if it is, you record the unmet need so the signal is not thrown away.

Every other DataHub skill assumes the asset exists. This one handles the case where the
search came back empty — which is the moment an agent is most likely to be confidently
wrong.

**The core discipline: an empty result is not evidence of absence.** It is far more often
evidence that the search was wrong — a synonym, a glossary term, a different platform, a
column rather than a table, a deprecated asset, or a data product wrapping the thing. You
must rule those out before you say the words "does not exist". An agent that declares a
table absent after one query will send someone to rebuild an asset that already exists,
which is worse than returning nothing.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex,
Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:** the full disproof procedure, the absence report, and the
recording step, via MCP tools or the DataHub CLI.

**Claude Code-specific features** (other agents can safely ignore these): `allowed-tools`
in the YAML frontmatter above.

**Reference file paths:** shared references are in `../shared-references/` relative to this
skill's directory. Skill-specific references are in `references/`.

---

## Mode 1 — Disprove the absence

Run this before you record anything, and before you tell anyone a thing does not exist.
Stop as soon as a step finds the asset; report it and switch to `/datahub-search`.

The full procedure, with the DataHub query for each step, is in
`references/absence-checklist.md`. In summary:

1. **Literal search.** The user's phrase, unmodified.
2. **Tokenised search.** Each significant term separately. `trial-to-paid conversion by
cohort` is four searches, not one: `trial`, `paid`, `conversion`, `cohort`.
3. **Glossary terms.** The organisation may name this concept differently from the user.
   A glossary hit usually points at the asset that carries the term.
4. **Column-level search.** The want is frequently a column on an asset that already
   exists, not a missing asset. Search fields as well as entities.
5. **Other platforms.** The user searched Snowflake; it lives in BigQuery, or in a
   dashboard, or a dbt model that has not been ingested.
6. **Deprecated and soft-deleted assets.** An asset that was removed is a different
   answer from an asset that never existed, and it usually has an owner to ask.
7. **Data products and domains.** The thing may be wrapped in a product whose name shares
   no tokens with the request.
8. **Lineage neighbours.** If a closely-related asset exists, walk one hop up and down.
   The want is often a trivial transform of something already catalogued.

**Only when all eight return nothing may you state that the asset is absent.**

## Mode 2 — Report the absence with its receipt

Never report a bare "not found". Report what you ruled out, so a human can audit the
claim and so the next agent does not repeat the work:

```
ABSENT: "monthly recurring revenue by segment"

Ruled out:
  literal search           0 results
  tokens (mrr, revenue,
    segment, monthly)      12 results, none matching the grain
  glossary terms           "MRR" exists, points at revenue_events (raw, not by segment)
  column search            no column named mrr on any catalogued asset
  platforms                searched all 4 connected platforms
  deprecated / removed     none
  data products            none
  lineage neighbours       revenue_events is upstream-adjacent; no segment dimension

Nearest existing asset: ecommerce.revenue_events (raw events, no segment grain)
```

The "nearest existing asset" line matters more than the absence itself. It is what the
person who builds this will start from.

## Mode 3 — Record the unmet need

An absence that is only reported is discarded. Record it so it accumulates.

**Ask which sink the organisation uses** — do not guess, and do not invent an entity type:

- **A structured property on the nearest existing asset or domain.** Works on stock
  DataHub today. Best when a nearest asset was identified.
- **An external tracker** (Jira, Linear, GitHub). Best when a human will act on it. Link
  the issue back to the nearest asset so the catalog carries the pointer.
- **A local log the caller aggregates.** Best for high-volume agent traffic where a
  ticket per miss is noise.

Record at minimum: the want as phrased, the requester identity, the timestamp, the
nearest existing asset, and the fields the requester needed. Requester identity should
come from the caller's authenticated identity, not from a field the caller types.

**If the same want is recorded repeatedly, say so.** Two independent requesters asking
for the same absent thing is a materially different signal from one, and it is the main
reason to record misses at all.

### A note on what this skill deliberately does not do

There is no first-class way to represent "an asset that does not exist" in the DataHub
metadata model today. This skill therefore records demand using existing primitives and
does not create placeholder entities in the catalog — a fake `dataset` for something that
does not exist pollutes search, lineage and assertions for every other consumer.

Whether demand should become a first-class entity is under discussion in
[RFC #19022](https://github.com/datahub-project/datahub/pull/19022). If that lands, this
skill's recording step should target it directly.

## Handoffs

- Asset turned out to exist → `/datahub-search`
- Asset exists but is undocumented, which is why it was not found → `/datahub-enrich`
- Asset was deprecated or removed → `/datahub-lineage` to find who depended on it
- Asset exists but is untrustworthy → `/datahub-quality`

## Failure modes to avoid

- **Declaring absence after one query.** The single most common and most damaging error.
- **Recording a want in the requester's private phrasing** with no nearest-asset anchor.
  It will never be matched against anything and becomes a dead row.
- **Creating a placeholder entity** so that the want is "in the catalog". Every other
  consumer of the catalog inherits it.
- **Trusting a `requester` field supplied by the caller.** Attribution that anyone can
  forge cannot be used to prioritise work.
