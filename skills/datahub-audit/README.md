# DataHub Audit

Run a systematic, read-only governance audit across a bounded DataHub catalog scope.

## What it checks

- Missing effective owners and descriptions, including editable overlays and siblings
- PII-looking fields without an existing classification
- Deprecated assets with active downstreams
- Orphan datasets with no lineage

The skill reports coverage, evidence, severity, scope, and limitations. It never writes
metadata; selected remediation is handed to `datahub-enrich` for a fresh before/after
plan and explicit approval.

## Usage

```text
/datahub-audit audit PROD Snowflake datasets
/datahub-audit how complete are owners and descriptions in the Finance domain?
/datahub-audit find unclassified PII candidates, limit 100 datasets
```

Or ask naturally: "Audit governance gaps in my DataHub catalog."
