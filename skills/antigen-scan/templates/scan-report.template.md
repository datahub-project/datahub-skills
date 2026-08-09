# Injection Scan Report

**Catalog:** <DATAHUB_GMS_URL>
**Scanned:** <timestamp>
**Sweep status:** Complete / **DEGRADED — not an all-clear**

## Scope

| Surface          | Count | Tool                                   |
| ---------------- | ----- | -------------------------------------- |
| Entities swept   | <n>   | `search` → `get_entities`              |
| Documents swept  | <n>   | `search_documents` → `grep_documents`  |
| Entities skipped | <n>   | already tagged `injection-quarantined` |

> If the sweep was DEGRADED, stop here. Record `degraded_reasons` verbatim below and
> report that the sweep could not complete — not that the catalog is clean.

## Findings

**<n> injection loci flagged** · **<n> hidden in zero-width Unicode**

| #   | URN     | Locus                                                 | Field          | Signals                                     | Hidden Unicode | Source tool    |
| --- | ------- | ----------------------------------------------------- | -------------- | ------------------------------------------- | -------------- | -------------- |
| 1   | `<urn>` | entity-description / column-description / kb-document | `<field_path>` | `instruction-override`, `data-exfiltration` | yes / no       | `get_entities` |

Signals are fixed category labels. Payload text is deliberately not reproduced here.

## By locus

| Locus              | Count |
| ------------------ | ----- |
| Entity description | <n>   |
| Column description | <n>   |
| KB document        | <n>   |

## Assessment

- **Highest-signal findings:** <which, and why — e.g. zero-width evasion indicates intent>
- **Suspected entry path:** <human edit / ingestion source / automation — if a hit is on an
  entity nobody edits by hand, the source will re-poison it after a cure>
- **Not established by this scan:** whether any agent read or acted on these fields.

## Recommended next step

Preview the remediation without writing anything:

```bash
python -m antigen cure --dry-run
```

No mutation has been performed. This report is read-only.
