# datahub-audit

Generate a reproducible, read-only coverage report for a scoped set of DataHub
entities. The skill reports effective metadata coverage, exact gaps, server
limitations, and a prioritized repair queue without mutating the catalog.

## Usage

```text
/datahub-audit how complete are our production Snowflake datasets?
/datahub-audit which Finance datasets lack owners or descriptions?
/datahub-audit audit these dataset URNs for lineage and quality evidence
```

The full workflow is in [`SKILL.md`](SKILL.md), and the suggested report shape
is in [`templates/audit-report.template.md`](templates/audit-report.template.md).
