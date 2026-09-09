# DataHub Audit

Measure metadata coverage and governance readiness across a declared DataHub scope.

## What it does

1. Defines the entity population and audit rubric
2. Fetches complete or explicitly sampled metadata through MCP or CLI
3. Deduplicates dataset siblings into logical assets
4. Calculates evidence-backed coverage with visible denominators
5. Produces a prioritized, read-only remediation backlog

## Capabilities

- Description, ownership, and domain coverage
- Column documentation coverage
- Tag and glossary-term policy coverage
- Sibling-aware logical asset scoring
- Platform/domain breakdowns
- Reproducible full or sampled audits

## Usage

```text
/datahub-audit audit PROD Snowflake datasets
/datahub-audit how complete is metadata in the Finance domain?
/datahub-audit generate a column documentation report for dbt models
/datahub-audit which critical assets are missing owners?
```
