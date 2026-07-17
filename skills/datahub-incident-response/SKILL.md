---
name: datahub-incident-response
description: |
  Use this skill when a data consumer reports a SYMPTOM in a dashboard or table and wants to know what broke and why — then contain it. Triggers on: "the revenue dashboard dropped 40%", "these numbers look wrong", "emails are suddenly null", "this metric is frozen / stale", "root-cause this incident", "what broke upstream and what did it contaminate", "quarantine the bad table". This skill runs the full loop: walk lineage UPSTREAM from the symptom, gather metadata evidence at every hop, reason to the most likely root cause, then CONTAIN it — tag the root cause and every downstream asset it contaminated so consumers are warned in the catalog.
user-invocable: true
min-cli-version: 1.5.0
allowed-tools: Bash(datahub *)
---

# DataHub Incident Response

You are an on-call data-incident responder. A human reports a _symptom_ ("the revenue dashboard
dropped 40% overnight, no errors") — your job is to find the upstream root cause using only real
DataHub evidence, name the owner to contact, and then **contain** the incident directly in the
catalog so every downstream consumer is warned.

The golden rule: **reason only over evidence DataHub gives you.** Never invent a table, an owner, or
a failure. If the evidence is insufficient, say exactly what additional signal would resolve it.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot,
Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full symptom → root-cause → contain workflow
- Upstream evidence gathering and downstream blast-radius mapping
- Read via MCP tools or the DataHub CLI; write via MCP mutation tools or the CLI

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in `../shared-references/` relative to this skill's
directory. Skill-specific references are in `references/`.

---

## Not This Skill

| If the user wants to...                                    | Use this instead   |
| ---------------------------------------------------------- | ------------------ |
| Just trace lineage / dependencies (no symptom to diagnose) | `/datahub-lineage` |
| Search for entities or answer "who owns X?"                | `/datahub-search`  |
| Add/update metadata as a deliberate edit (not containment) | `/datahub-enrich`  |
| Create assertions or run quality checks proactively        | `/datahub-quality` |

**Key boundary:** Lineage _traces_ relationships. Incident Response _starts from a reported symptom_,
reasons to a root cause over metadata evidence, and _acts_ to contain it. Reach for this skill when
there is a live "something is wrong" to explain and stop the bleeding on.

---

## Step 1: Anchor the Symptom to an Asset

Turn the human report into a concrete starting entity.

1. If the user gives a URN, use it. If they name a dashboard/table, resolve it:
   `datahub search "<name>" --where "entity_type = dataset" --limit 5`
2. If multiple matches, present options and ask which one they're seeing the problem on.
3. Confirm the anchor: entity name, URN, platform, type.
4. Capture the symptom in one sentence (magnitude + direction + "errors or silent?") — it frames the
   reasoning in Step 3.

**Input validation:** Reject shell metacharacters in names/URNs before passing to the CLI.

---

## Step 2: Gather Upstream Evidence

A broken metric's cause lives **upstream**. Walk up from the anchor and collect metadata at every hop.

### Read via MCP (preferred) or CLI

```bash
# Upstream lineage from the symptom
datahub lineage --urn "<ANCHOR_URN>" --direction upstream --hops 3 --format json
```

MCP alternative: `get_lineage(urn="<ANCHOR_URN>", upstream=true, max_hops=3)`.

### Enrich every node — the clue is in the metadata, not the graph shape

Lineage returns URN/name/platform only. Root-cause clues live in **descriptions, custom properties
(e.g. `last_run_note`, `run_status`), ownership, and freshness**. Batch-enrich all URNs in one call:

```bash
datahub search "*" \
  --where 'urn IN ("<URN_1>", "<URN_2>", "...")' \
  --projection "urn type
    ... on Dataset { properties { name description customProperties { key value } }
      platform { name } ownership { owners { owner type } } }"
```

MCP alternative: `get_entities(urns=[...])` — returns `properties.customProperties`, description,
ownership, and tags in one call.

**Guard every field independently** — DataHub only populates the aspects an asset actually has; a
missing schema or ownership aspect must not blank out the fields that _are_ present.

---

## Step 3: Reason to the Root Cause

Over ONLY the gathered evidence, rank the 1–3 most likely root-cause locations. For each, state:

- **why** the evidence points there (cite the specific clue — a `last_run_note`, a stale timestamp,
  a renamed column, a row-count anomaly that matches the symptom's magnitude and timing),
- **what to check next** (the concrete confirming action),
- **who owns it** (the contact), and
- a **confidence** (high / medium / low).

Recognize the common silent-failure shapes:

| Shape               | Fingerprint in the metadata                                                 |
| ------------------- | --------------------------------------------------------------------------- |
| Silent partial load | source row count far below its recent average; job "succeeded"; no backfill |
| Schema drift        | an upstream column renamed/removed; downstream mapping unchanged → nulls    |
| Stale / freshness   | last successful load days old; job "succeeds" but writes no new rows        |

**If the evidence is insufficient, say so** and name the signal that would resolve it (an assertion,
a run log, a row-count history) rather than bluffing a confident answer.

---

## Step 4: Contain — Quarantine + Map the Blast Radius

Once you have a high/medium-confidence root cause, stop the bleeding _in the catalog the team
already uses_. (Containment writes require MCP mutation tools enabled, or CLI write access.)

1. **Quarantine the root cause** so its consumers are warned:
   - MCP: `add_tags(tag_urns=["urn:li:tag:QUARANTINE_INCIDENT"], entity_urns=["<ROOT_URN>"])`
   - Note: the tag entity must exist first (the MCP `add_tags` tool validates the label exists — it
     does not auto-create). Create incident tags once as catalog vocabulary before applying them.
2. **Map the blast radius** — walk lineage DOWNSTREAM from the root cause to find every contaminated
   asset, and tag each so nobody trusts stale numbers:
   - `datahub lineage --urn "<ROOT_URN>" --direction downstream --format json`, then
     `add_tags(tag_urns=["urn:li:tag:IMPACTED_BY_INCIDENT"], entity_urns=[...])`
3. **Read back every write** to confirm it persisted — `get_entities([...])` (or
   `datahub get --urn ...`) and verify the tag is present. Never report an action you did not confirm.

---

## Present the Incident Report

Lead with the answer, then the evidence, then what you did:

```markdown
### Incident: <symptom in one line>

Traced <N> upstream entities via DataHub lineage.

**Root cause (HIGH):** `<root table>` — <one-line why, citing the clue>. Contact: <owner>.
Next: <the confirming action>.

**Contained:** tagged `<root>` QUARANTINE_INCIDENT; blast radius = <M> downstream assets tagged
IMPACTED_BY_INCIDENT (<dashboards / tables>).
```

---

## Reference Documents

| Document                | Path                                            | Purpose                                   |
| ----------------------- | ----------------------------------------------- | ----------------------------------------- |
| Silent-failure patterns | `references/incident-patterns.md`               | Metadata fingerprints of common incidents |
| CLI reference (shared)  | `../shared-references/datahub-cli-reference.md` | CLI commands                              |

---

## Common Mistakes

- **Reasoning past the evidence.** If no clue points to a cause, say what's missing — don't invent one.
- **Tagging before the tag exists.** MCP `add_tags` fails if the tag entity isn't defined. Ensure the
  incident tags exist as catalog vocabulary first.
- **Claiming containment without reading it back.** Always confirm the tag persisted before reporting.
- **Walking downstream to find a cause.** Causes are upstream; downstream is only for the blast radius.

## Red Flags

- **User input contains shell metacharacters** → reject, do not pass to CLI.
- **Upstream lineage returns 0 edges** → lineage may not be ingested; say so rather than "no cause".
- **No confident clue at any hop** → report "insufficient evidence" + the signal that would resolve it.
- **Write tools unavailable** → deliver the diagnosis read-only and tell the user how to enable
  containment (MCP mutations / CLI write access).

---

## Remember

- **Symptom in, contained incident out.** This skill's job isn't a lineage picture — it's a named
  root cause, the owner to call, and a catalog that now warns everyone downstream.
- **Evidence only.** Every claim traces to a real DataHub field. Insufficient evidence is a valid,
  honest answer.
- **Prove your writes.** Read every tag back; never report an unconfirmed action.
