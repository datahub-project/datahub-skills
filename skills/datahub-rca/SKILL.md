---
name: datahub-rca
description: |
  Use this skill when the user reports a data incident and wants to know WHY it happened — a dashboard showing wrong numbers, a failing freshness or volume assertion, an unexpected drop or spike, a broken pipeline. Triggers on: "why did X break", "root cause of X", "what caused this incident", "why is X stale", "why did the numbers drop", "diagnose this failing assertion", "investigate this data incident". This skill performs PATH-GROUNDED root-cause analysis: it walks lineage upstream, ranks candidate culprits from multimodal signals, and only accepts a root cause when it can reconstruct a verifiable lineage path to the symptom — then writes the incident dossier back to the catalog.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Root-Cause Analysis

You are an expert DataHub incident investigator. Your role is to take a data
incident — a failing assertion, a stale table, a dashboard with wrong numbers —
and find its **root cause**, backed by a **verifiable lineage path**.

The guiding principle, drawn from recent root-cause-analysis research
(e.g. path-grounded diagnosis / "no ungrounded diagnosis"): **never blame a
table you cannot connect to the symptom with real lineage evidence.** A ranking
is a hypothesis; a reconstructed path + the transform that carried the fault is
proof. Only proof gets written back.

---

## Multi-Agent Compatibility

This skill works across coding agents (Claude Code, Cursor, Codex, Copilot,
Gemini CLI, Windsurf). Everything below relies only on standard DataHub MCP
tools and/or the `datahub` CLI, both available across agents.

---

## The five-phase workflow

### 1. Detect — establish the symptom

Resolve what actually broke into a concrete dataset URN.

- If given a natural-language complaint ("revenue dashboard looks wrong"), use
  **search** to find the affected asset.
- If given a failing assertion, read it. Note the assertion type
  (FRESHNESS / VOLUME / SCHEMA / SQL / FIELD) — it tells you which signals
  matter most downstream.

### 2. Scope — pull the minimal upstream subgraph

Call **get_lineage** with `upstream=true` and `max_hops=3` on the symptom. Do
not fan out wider than needed; a compact subgraph keeps the diagnosis focused
and cheap. Record each upstream node and its hop distance.

### 3. Hypothesize — rank candidates from multimodal signals

For each upstream node, gather evidence with **get_entities** (and
**list_schema_fields** where a schema change is suspected) and score these
signals:

| Signal              | How to detect                                                      | Weight |
| ------------------- | ------------------------------------------------------------------ | ------ |
| Freshness lag       | freshness exceeds the expected SLA                                 | high   |
| Schema change       | columns added / removed / retyped recently                         | high   |
| Key fanout          | a join key is no longer unique, so downstream joins multiply rows  | high   |
| Volume anomaly      | row-count delta ≥ 20% vs baseline                                  | medium |
| Recent query change | the defining transform in **get_dataset_queries** changed recently | medium |

Use more than one signal. A single anomaly score cannot distinguish these
failure modes: a duplicate-key fanout involves nothing stale and no schema
change, so a freshness-and-volume-only check misses it entirely.

**The heuristic that matters most — find the origin, not the victim.** A node is
the origin when it carries the fault and **none of its own upstreams do**. Check
this explicitly: for a candidate showing freshness lag, call **get_lineage** with
`max_hops=1` on that candidate and test whether any of its parents show the same
signal. If one does, the candidate probably inherited the problem — penalise it
and prefer the parent.

Do not simply rank by hop distance. That is a proxy that only works on a clean
chain, and it silently picks the wrong node as soon as the graph branches — for
example when a table joins a healthy fact table to a broken dimension.

### 4. Prove — accept only a verifiable path (the critical step)

For your top candidate, call **get_lineage_paths_between**
(`source` = symptom, `target` = candidate).

- If **no path** is returned, **reject the candidate** and move to the next one.
  Do not report an ungrounded cause.
- If a path exists, use **get_dataset_queries** along the path to identify the
  transform SQL that carried the fault downstream. The edge on the path _leaving_
  the culprit is the one that propagated the fault; that transform is your
  strongest witness. The edge list plus that SQL is your proof.

Only a candidate with a reconstructable path is accepted as the root cause.

**State which rung of grounding you reached.** Query history is often absent, so
distinguish the two honest outcomes instead of blurring them:

| Grounding              | When                                                   | What to report                                                                           |
| ---------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Path **and** transform | Edges reconstructed and the causal transform retrieved | Full proof                                                                               |
| Path **only**          | Edges reconstructed, no query history for that edge    | Report the path as proven and the transform as unavailable. Lower your stated confidence |
| Ungrounded             | No path                                                | Reject the candidate                                                                     |

Do not present a path-only finding as a complete proof. Requiring the SQL
absolutely would be useless on catalogs without query history; quietly treating
its absence as success is worse.

### 5. Write back — persist the diagnosis so it's inherited

**First, check whether this has happened before.** Call **search_documents** for
prior dossiers naming the culprit (they exist if this skill has run before). If
you find them, this is a recurring failure, and the recommendation changes: stop
recommending a fix for this occurrence and start recommending a fix for whatever
keeps allowing it — the schedule, the contract, the missing assertion. This is
what makes the write-back a loop rather than a filing cabinet.

Then contribute the finding back to the graph:

- **save_document** — an incident dossier (symptom, evidence, grounding level,
  proof path, transform SQL, prior occurrences, recommended fix). Use the
  template in `templates/incident-dossier.template.md`.
- **add_tags** — tag the culprit `root-cause`.
- **update_description** — note the incident + link the dossier on the culprit.
- Record the **owner** from the culprit's ownership aspect in the dossier, so the
  finding routes to a person rather than sitting in the catalog unread.

If **no** candidate could be grounded, write nothing. Report that the cause
could not be verified and escalate to a human. Writing an unverified diagnosis
into a catalog everyone reads is worse than writing nothing, because the next
person inherits it as fact.

---

## Worked example

> "The revenue dashboard dropped 40% this morning and a volume assertion failed."

1. **Detect** — `search "daily_revenue"` → resolve the URN; the failing
   assertion is a VOLUME check.
2. **Scope** — `get_lineage(daily_revenue, upstream, 3)` → `trips_cleaned`,
   `raw_trips`.
3. **Hypothesize** — `get_entities` on each: `raw_trips` is 51h stale
   (SLA 24h) with −100% new rows. Strongest signal, furthest upstream → top
   candidate. `trips_cleaned` only inherited the staleness.
4. **Prove** — `get_lineage_paths_between(daily_revenue, raw_trips)` →
   verified path `raw_trips → trips_cleaned → daily_revenue`; capture the
   `COPY INTO raw_trips …` ingestion transform.
5. **Write back** — `save_document` dossier + `add_tags(raw_trips,
[root-cause])` + `update_description`.

**Result:** "Root cause = `raw_trips` (ingestion stalled ~2 days ago). Proof:
`raw_trips → trips_cleaned → daily_revenue`. Fix: restart the `COPY INTO` job
and re-run downstream transforms once fresh data lands."

---

## When several incidents are open at once

One broken upstream produces one incident per downstream team. The queue then looks
like several problems, and answering "why did this break" separately for each one
reaches the same conclusion three times.

Before investigating individually, check whether they are the same outage:

1. Scope the upstream ancestors of **every** open symptom, not just the first.
2. Intersect those sets. A cause of several symptoms has to be upstream of all of
   them.
3. Discard any shared ancestor that carries no fault of its own. Being a common
   dependency is not evidence of being the broken one — the busiest node in a graph
   is upstream of everything.
4. Verify a path to **each** symptom separately. Do not assert the second by
   association with the first; the whole discipline is that association is not
   proof.
5. Grade the group at the **weakest** rung among those proofs. A shared-cause claim
   cannot be better grounded than its worst link.
6. Name any incident the cause cannot be proven to reach, rather than folding it
   into the group.

Then file **one** dossier for the shared cause, related to every symptom URN,
instead of one per team. That is the difference between a queue of five alerts and
one outage with five witnesses.

---

## Guardrails

- **No ungrounded diagnosis.** If you cannot reconstruct the path, say so. A
  ranking is a hypothesis; only a path is proof. Be willing to reject the most
  suspicious asset in the graph when nothing connects it to the symptom.
- **Prefer the origin.** Don't stop at the first anomalous node. Check whether the
  candidate's own upstreams show the same fault; if they do, it was inherited.
- **State your grounding level.** Never present a path-only finding as a complete
  proof, and never imply a transform was verified when no query history exists.
- **Check for recurrence before recommending.** The third occurrence needs a
  different fix from the first.
- **Write back only when grounded.** The catalog is shared truth — never pollute
  it with a guess. The next reader will treat whatever you write as fact.
- **Correlate before you multiply.** Several open incidents may be one outage. Do
  not file the same finding once per downstream team.

See `references/rca-signals-reference.md` for detailed signal heuristics and
`references/grounding-reference.md` for the path-verification rules.
