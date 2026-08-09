# Remediation Plan — approval required

**Source:** `python -m antigen cure --dry-run` · **Nothing has been written.**

## Scope

|                                      |                     |
| ------------------------------------ | ------------------- |
| Loci to remediate                    | <n>                 |
| Surgical (`excise`)                  | <n>                 |
| **Whole-field (`quarantine-field`)** | **<n>**             |
| Mutations that will be issued        | <n × 4>             |
| Target catalog                       | `<DATAHUB_GMS_URL>` |

## Planned mutations

| #   | URN                 | Field          | Tool                        | Mode   | Before → After                                                          |
| --- | ------------------- | -------------- | --------------------------- | ------ | ----------------------------------------------------------------------- |
| 1   | `<urn>`             | `<field_path>` | `update_description`        | excise | injected span deleted; rest of the description preserved                |
| 2   | `<urn>`             | —              | `add_tags`                  | —      | `injection-quarantined`                                                 |
| 3   | `<urn>`             | —              | `add_structured_properties` | —      | `antigen.contentSha256`, `antigen.payloadSha256`, `antigen.lastScanned` |
| 4   | `Antigen/Incidents` | —              | `save_document`             | —      | forensic record, hashes only                                            |

## What you are approving — read before answering

- **<n> descriptions will be replaced in full.** For every `quarantine-field` locus the
  entire description is replaced by an inert banner. Antigen does not keep a copy. The
  prior text is recoverable from DataHub's aspect version history and from nothing
  Antigen writes.
- **<n> descriptions will be edited surgically.** For `excise` loci the injected span is
  deleted and the legitimate documentation survives.
- **Nothing recoverable is written to the graph.** The forensic record holds hashes only.
- **Quarantined entities are skipped by future sweeps**, which is what makes re-running
  safe — and also why re-planting test payloads without a catalog reset finds nothing.

## Options

| To...                                                                  | Run                                                 |
| ---------------------------------------------------------------------- | --------------------------------------------------- |
| Apply everything above                                                 | `python -m antigen cure --apply`                    |
| Apply only the surgical half, hold whole-field quarantines for a human | `python -m antigen cure --apply --only-mode excise` |
| Change nothing                                                         | do nothing — this was a preview                     |

**Approve these <n> mutations against the live catalog?**
