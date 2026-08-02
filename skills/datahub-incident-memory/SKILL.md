---
name: datahub-incident-memory
description: |
  Give incident response institutional memory. When a data incident is resolved,
  file the diagnosis back onto the affected assets as a structured-property
  memory record; when a new incident appears, recall matching records from the
  asset and its upstream lineage BEFORE diagnosing from scratch. Repeat
  incidents resolve in seconds instead of minutes. Use when the user says
  "remember this incident", "have we seen this before?", "file this diagnosis",
  or wants incident response that gets faster over time.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Incident Memory

Data incidents repeat. The second `not_null` failure on the same column has the
same root cause as the first one — but without memory, every responder (human or
agent) re-derives it from scratch. This skill makes the DataHub graph itself the
memory: resolved diagnoses are written to the affected assets as structured
properties, and new incidents are checked against that memory **first**.

This is a *resolution* memory, not an alert memory: it stores how the incident
was **fixed**, not just that it was seen. It is distinct from audit/history
skills — the payoff is recall speed on the next infection, not a record trail.

## Not This Skill

- Creating or running assertions, subscribing to incident notifications →
  `datahub-quality`
- Exploring lineage for its own sake → `datahub-lineage`
- General metadata updates (tags, terms, owners) → `datahub-enrich`

## Prerequisites

- DataHub connection configured (`datahub-setup`) and the MCP server available.
- One-time: the memory structured property must exist (Step 0).

## Step 0: Ensure the memory property exists (one-time)

```bash
datahub properties upsert -f incident-memory-property.yaml
```

with `references/incident-memory-property.yaml`:
qualifiedName `io.datahub.incidentMemory`, valueType string, cardinality
MULTIPLE, entityTypes: dataset. Each value is one JSON memory record (schema in
`references/memory-record-schema.md`).

## Step 1: Fingerprint the incident

Normalize the symptom into a deterministic fingerprint so "the same infection"
is machine-checkable:

```
fingerprint = sha256(failure_class | lowercase(dataset_urn) | sorted(columns))
```

`failure_class` is the assertion/test type (`not_null`, `unique`,
`accepted_values`, `freshness`, `missing_column`, …). Two incidents with equal
fingerprints are the same symptom on the same asset.

## Step 2: Recall BEFORE diagnosing

Query memory records on the affected asset **and its upstream lineage** (the
infection often travelled the same path before):

1. Read `io.datahub.incidentMemory` values on the affected dataset —
   **direct entity get by URN, never search** (search indexes update
   asynchronously after writes; URN reads are consistent).
2. `get_lineage` (MCP, direction UPSTREAM) → read memory records on each
   upstream asset the same way.
3. Match ladder, strongest first — report the strength with the match:
   - `exact` — same fingerprint on the asset
   - `class_on_asset` — same failure class, same asset, different columns
   - `class_on_upstream` — same failure class on an upstream asset
   Break ties by recency.

**On a hit:** present the memory to the user before any fresh diagnosis:

```markdown
## Memory recall — seen before

**Match:** exact (fingerprint fp-…) on `<asset>`
**Prior incident:** <id>, resolved <when> in <MTTR>
**Root cause then:** <root_cause>
**Fix then:** <fix_summary>

Proceed with the known fix, or re-diagnose from scratch?
```

**On a miss:** say "no incident memory found — cold diagnosis" and proceed with
normal root-cause analysis (`datahub-lineage` patterns). If the graph lacks the
context to diagnose (no lineage, unknown asset), say so explicitly and stop —
an honest escalation beats a fabricated root cause.

## Step 3: Build the write-back plan (approval)

After resolution, follow the standard enrichment approval flow — show the plan
before mutating anything:

```markdown
## Incident Memory Plan

| Write | Target | Value |
| ----- | ------ | ----- |
| structured property `io.datahub.incidentMemory` | <affected asset> | memory record JSON |
| structured property `io.datahub.incidentMemory` | <root-cause asset> | same record |
| tag `incident-memory` | both assets | — |
| resolve incident | <incident urn> | closing message |
```

Write the record to the affected asset **and** the root-cause asset so recall
works from either direction of lineage.

## Step 4: Execute and verify

Execute via `add_structured_properties` (MCP) or the SDK patch builder. Then
**verify by reading the record back by URN** before reporting success — never
assume the write landed, and never verify through search.

## Memory record schema (summary)

```json
{
  "memory_id": "im-…", "fingerprint": "fp-…",
  "failure_class": "not_null", "dataset_urn": "…", "columns": ["amount"],
  "source_incident": "…", "root_cause": "…", "fix_summary": "…",
  "blast_radius_urns": ["…"], "mttr_seconds": 252, "created_at": "ISO-8601"
}
```

Full schema and rationale: `references/memory-record-schema.md`.
