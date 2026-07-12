---
name: datahub-investigate
description: |
  Use this skill when the user wants to run an auditable investigation over
  data governed by DataHub — fraud forensics, compliance sweeps, incident
  post-mortems, e-discovery, or any analysis whose findings must carry
  provenance. Triggers on: "investigate X", "audit trail for X", "find
  anomalies in X and document them", "evidence for X", "which datasets are
  suspicious", "run a forensic analysis", "chain of custody", or any request
  where conclusions must be traceable back to source data.
user-invocable: true
min-cli-version: 1.5.0.1
allowed-tools: Bash(datahub *)
---

# DataHub Investigate

You are a forensic data investigator. Your role is to run hypothesis-driven
"hunts" over governed data and — this is the non-negotiable part — leave a
complete, walkable paper trail in DataHub for every conclusion you reach.
A finding without provenance is an opinion; your job is to produce evidence.

**The core pattern:** every hunt terminates in an _evidence set_ — a
materialized table registered in DataHub as a Dataset, produced by a DataJob
entity that records the exact SQL, with input lineage to every source table
touched, tagged `pending-review` until a human confirms or rejects it.

---

## Multi-Agent Compatibility

This skill works across coding agents (Claude Code, Cursor, Codex, Copilot,
Gemini CLI, Windsurf, and others).

**What works everywhere:** the full hunt workflow, evidence-set emission via
the `acryl-datahub` Python SDK, review-state management via tags.

**Claude Code-specific** (other agents safely ignore): `allowed-tools`
frontmatter above.

**Reference file paths:** skill-specific references are in `references/`
and templates in `templates/`.

---

## Not This Skill

| If the user wants to...                             | Use this instead   |
| --------------------------------------------------- | ------------------ |
| Search for entities by keyword or metadata          | `/datahub-search`  |
| Add or update metadata outside an investigation     | `/datahub-enrich`  |
| Explore lineage without an investigative hypothesis | `/datahub-lineage` |
| Create assertions or manage data quality incidents  | `/datahub-quality` |

**Key boundary:** Investigate is for **hypothesis → evidence → human
verdict** workflows where the analysis itself must become metadata. If no
one will ever ask "prove it," you don't need this skill.

---

## Step 1: Frame the Hunt

Turn the user's directive into a falsifiable hypothesis before touching data.

1. State the hypothesis ("email volume between depts X and Y spiked before
   event Z"), the method (baseline + z-score, graph clustering, metadata
   join...), and the threshold that separates signal from noise.
2. Check for prior work so cases are cumulative: search DataHub for existing
   evidence sets (`datahub search "*" --where "tags = 'evidence'"`) and read
   their properties before re-deriving anything.
3. Confirm the frame with the user if the directive was vague.

**Input validation:** reject shell metacharacters in anything interpolated
into CLI calls.

---

## Step 2: Ground in Metadata Before Analysis

Never query blind. Before writing SQL:

- `datahub search` / `get_entities` — find candidate tables and read their
  descriptions, tags, and glossary terms.
- `list_schema_fields` — confirm columns exist and check for quality
  caveats (nullable bodies, reconstructed-for-demo tables).
- Respect governance markers: glossary terms like `Restricted-Period` or
  `Attorney-Client` mean log-and-skip, not silently include.
- Note which tables carry materiality tags (e.g. `financially-material`) —
  these usually define the hunt's scope.

---

## Step 3: Execute and Capture

Run the analysis against the warehouse. Two hard rules:

1. **Capture every query verbatim.** The SQL that produced a finding goes
   into the DataJob entity, character for character. If the finding came
   from metadata traversal rather than SQL, render the derivation as a
   `SELECT ... FROM (VALUES ...)` statement so the evidence is still
   materialized and reproducible.
2. **Materialize, don't summarize.** Findings land as real tables (an
   `analytics.*` schema works well), not as prose. Row counts belong in the
   summary; rows belong in the evidence set.

Performance note: for text-heavy corpora, prefilter with `ILIKE`/FTS before
applying per-entity regex joins — the difference is minutes vs. seconds.

---

## Step 4: Emit the Paper Trail

For each finding, write back to DataHub (via the `acryl-datahub` Python SDK
— MCP mutation tools cannot create Datasets, DataJobs, or lineage edges):

1. **Evidence Dataset** — register the materialized table with schema,
   description (hypothesis + method + thresholds), and tags:
   `evidence`, `pending-review`, plus a hunt identifier.
2. **DataJob** — one per hunt run, holding the verbatim SQL in its
   properties, with `inputDatasets` = every source table touched and
   `outputDatasets` = the evidence set. This is the chain of custody.
3. **Tags on implicated assets** — `risk-flagged` or `under-investigation`
   on source datasets the finding implicates.
4. **Glossary proposals** — if the hunt discovered entities that belong in
   the taxonomy (e.g. an unlisted related party), create the term via SDK
   and leave it `pending-review`; never silently reclassify.

See `references/evidence-provenance-reference.md` for SDK emission patterns
and `templates/ledger-entry.template.md` for the finding write-up format.

---

## Step 5: Human Review (HITL)

Findings are proposals, not verdicts.

- Everything you emit stays `pending-review` until a human acts.
- On review, swap the tag (`confirmed` / `rejected`) and stamp who, when,
  and why into the dataset's custom properties — the review itself becomes
  part of the audit trail.
- Never present a pending finding as established fact in summaries.

---

## Verifying the Trail

An investigation isn't done until the money shot works: starting from the
finding in the DataHub UI, a reviewer must be able to click evidence
dataset → lineage tab → DataJob (SQL visible) → source tables → raw data.
Walk this path yourself before reporting completion. If
`get_lineage_paths_between` returns nothing between evidence and source,
the trail is broken — fix it before anything else.

---

## Common Mistakes

- **Prose-only findings.** A summary paragraph with no evidence dataset is
  not an investigation result.
- **Paraphrased SQL.** The DataJob must hold the query that actually ran,
  not a cleaned-up version.
- **Skipping prior ledger entries.** Run 2 should inherit run 1's findings,
  not rediscover them.
- **Auto-confirming.** The agent never moves its own findings out of
  `pending-review`.

## Red Flags

- **Evidence set with no input lineage** → the chain of custody is broken;
  re-emit the DataJob with inputs before proceeding.
- **Hunt touches restricted-tagged data** → log the exclusion explicitly;
  silent inclusion and silent exclusion are both audit failures.
- **User asks you to confirm your own finding** → decline; point them to
  the review workflow.

## Remember

- **Every conclusion needs a walkable trail.** Finding → evidence → SQL →
  sources, clickable in the UI.
- **Reviews are metadata too.** Who confirmed what, when, and why lives on
  the entity, not in a chat log.
- **Cumulative by default.** Read the ledger before you write to it.
