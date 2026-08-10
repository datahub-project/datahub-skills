# Remediation reference

Exactly what Antigen writes to DataHub, through which tool, and what each write costs. Use this to answer "what will this do to my catalog?" before the approval gate.

## The four write-backs per finding

`cure` chains four Agent Context Kit mutation tools per locus, in this order.

### 1. `update_description` — the defuse

Reconstructs the field with the injected span **deleted** — not quoted, not commented out. A quoted imperative is still an imperative a model can obey, so quarantining by quoting would not be a fix.

An inert banner is appended:

```text
> ⚠ Antigen: a prompt-injection payload was removed from this field on <date>.
  Forensic evidence: <handle>. Detection signals: recorded in the Antigen incident
  record `antigen-incident-<id>` (the category labels are not repeated here — they
  are detector triggers themselves).
```

The banner contains no imperative, no payload text, **and no detection category label**. The labels used to be interpolated inline, and that broke convergence: labels like `reveal-secret` are phrases the detector's own rules score on, so the banner re-flagged the field it had just cured. Entity loci were shielded by the quarantine tag; KB documents were not, and looped forever. The labels now live only in the forensic incident record, which the sweep exempts by title, and `inert_banner` scores the exact text before writing it so the invariant holds structurally.

The tamper-evidence hash is computed over the text **before** the banner marker, so the banner itself never perturbs the hash and a later edit to the real content still trips drift detection.

Field-level findings pass `column_path`, so a poisoned column description is edited at column scope rather than replacing the entity description.

### 2. `add_tags` — quarantine

`injection-quarantined` on the poisoned entity.

This tag is also what makes the workflow idempotent: `scan` skips entities already carrying it, so `scan && cure` run twice with no state reset is a no-op. It also means **re-planting test payloads without a reset finds nothing** — reset the instance first.

### 3. `add_structured_properties` — tamper evidence

| Property                | Contents                                                                                                       |
| ----------------------- | -------------------------------------------------------------------------------------------------------------- |
| `antigen.contentSha256` | Hash of the cleaned content (banner excluded). What `rescan` re-computes to detect drift.                      |
| `antigen.payloadSha256` | An **irreversible** hash of the removed payload. Forensic correlation only — nothing can be recovered from it. |
| `antigen.lastScanned`   | Timestamp of the remediation.                                                                                  |

These properties need their definitions emitted once before any cure (`python -m antigen.register_properties`) — `add_structured_properties` rejects a property that has no definition. That registration is a base `acryl-datahub` emit, not an Agent Context Kit tool call.

### 4. `save_document` — the forensic record

Files an incident record into `Antigen/Incidents` containing **hashes only** — the payload digest, the cleaned-content digest, the remediation mode, the timestamp, and the detection signal labels. No payload text, plaintext or encoded, is ever written to the graph.

For KB-document findings this same tool also overwrites the poisoned document **in place**, addressed by URN. The URN matters: omit it and DataHub mints a _new_ document, leaving the poisoned original readable.

## The two remediation modes

| Mode               | Trigger                                           | Effect on the field                                                                                            | Safe to automate?                             |
| ------------------ | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `excise`           | A fixture records the field's original clean text | Injected span deleted; legitimate documentation survives                                                       | Yes — `--only-mode excise` restricts to these |
| `quarantine-field` | No fixture — the ordinary case on a real catalog  | The **entire field** is replaced by the banner; legitimate documentation in it is lost from the current aspect | No — hold for a human                         |

**Recovery.** Antigen does not keep a copy of anything it removes. That is deliberate: retaining a recoverable payload would defeat the purpose. The field's prior content survives only in **DataHub's native aspect version history** and in nothing Antigen writes.

**It is not one action per field.** That claim was disproved against a live DataHub GMS v1.7.0 ([`docs/false-positive-revert.md`](https://github.com/edycutjong/antigen/blob/main/docs/false-positive-revert.md), reproducible with `python scripts/revert_drill.py`). State the real cost before approving any `quarantine-field` locus:

- **Floor is 2 API calls** (timeline API: 1 read + 1 write); **4** via the version probe, because nothing exposes a version count — you walk versions until a 404.
- **"Restore version 1" is a silent trap.** DataHub numbers aspect versions **0 = latest, 1 = OLDEST**. Unless the field was written exactly twice, the one-call revert restores a superseded draft and returns **200 OK with no warning** — worse than the cure, because the operator believes the text is back.
- **Not per-field for columns.** All column descriptions share one `editableSchemaMetadata` aspect, so reverting one column silently rolls back a colleague's later edit to a _different_ column. Doing it safely means merging the single field into the _current_ aspect by hand.
- **Residue survives the text revert:** the `injection-quarantined` tag, the three `antigen.*` structured properties, and the incident documents. A later `scan` will **not** re-flag the restored field, because it skips quarantined entities — use `rescan`.
- **No UI path.** Live GraphQL introspection found 169 mutations and 106 queries, none of which restores an old aspect value. Recovery needs an engineer with API credentials.
- If the operator cannot confirm their **aspect-retention policy**, warn them: a non-default policy may have discarded the pre-cure value entirely, making recovery impossible rather than merely multi-step.

Antigen automates none of this. Budget a procedure, not a click.

## Blast radius

`blast-radius` walks `get_lineage` two hops downstream from each flagged entity and tags each downstream asset `injection-blast-radius:<source-urn>`.

The reason this matters more on DataHub than on a generic catalog: **Documentation Propagation is enabled by default in Open Source DataHub** and automatically copies column documentation to downstream and sibling columns along column-level lineage. A single poisoned column description can therefore reach many agent-readable surfaces with no further attacker effort. The blast-radius pass retraces exactly those edges.

Report it as **reach, not compromise.** A downstream tag means an agent reading that asset may have been exposed. Whether an agent acted on it is an audit-log question, and Antigen does not claim to answer it.

## Certification, and why it is not permanent

`certify` tags every clean entity `agent-safe-certified` **and** stamps `antigen.contentSha256` on it.

The stamp is what makes certification a standing control instead of a label that rots: `rescan` re-hashes every stamped entity — quarantined _and_ certified — so any later content change trips drift and re-flags the entity. Without the stamp, "certified" would mean "was clean at some point".

Volume warning: **2 mutations per clean entity**. On a 1,000-entity catalog that is roughly 2,000 writes. Always surface the count from `certify --dry-run` before approving.

## Antigen's own records are excluded by title, and that is a known weakness

The sweep skips documents whose title starts with `antigen-incident-`, because an incident record names the categories it remediated (`instruction-override`, `reveal-secret`) and those category names are themselves detector triggers — scanning its own ledger would re-flag it forever, and curing that would emit another record.

Documents created through the kit carry no author or provenance field, so the only available exclusion key is the title, which is **attacker-writable**: anyone who can create a KB document can name it with the reserved prefix and be skipped by the sweep. This trade-off is documented in `antigen/scan.py::is_own_incident`, and it is the subject of an open upstream discussion. Treat an unexpected finding under `Antigen/Incidents` as suspicious rather than routine.

## Write budget at a glance

| Command        | Writes                                | On a 1,000-entity catalog with 10 findings |
| -------------- | ------------------------------------- | ------------------------------------------ |
| `scan`         | 0                                     | 0                                          |
| `rescan`       | 0                                     | 0                                          |
| `cure`         | 4 per finding                         | ~40                                        |
| `blast-radius` | 1 tag per downstream asset per source | varies with lineage depth                  |
| `certify`      | 2 per **clean** entity                | ~1,980                                     |

`certify` is by far the most expensive command in the tool. Never run it as a reflex after a cure without showing the count first.
