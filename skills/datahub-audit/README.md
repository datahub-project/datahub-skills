# DataHub Audit

Systematic metadata coverage reports and governance health checks across your DataHub catalog.

## What it does

1. Defines the audit scope (entity type, platform, environment, domain)
2. Executes coverage queries across the catalog
3. Calculates metrics and percentages per dimension
4. Generates a structured report with actionable recommendations

## Audit types

**Coverage audit:** Measure how well entities are documented, owned, tagged, and classified.

**Governance audit:** Assess domain assignment, data product membership, deprecation hygiene, and PII classification coverage.

## Usage

```
/datahub-audit how complete is our metadata?
/datahub-audit which Snowflake tables lack descriptions?
/datahub-audit ownership coverage report for the Finance domain
/datahub-audit governance health check for PROD datasets
/datahub-audit how many tables have PII tags?
```

Or ask naturally: "audit our metadata coverage", "generate a quality report for BigQuery datasets".

## Files

| File | Purpose |
| --- | --- |
| `SKILL.md` | Main skill instructions |
| `references/audit-patterns-reference.md` | Query patterns for each coverage dimension |
| `templates/coverage-audit-report.template.md` | Full coverage report format |
| `templates/governance-audit-report.template.md` | Governance health report format |
