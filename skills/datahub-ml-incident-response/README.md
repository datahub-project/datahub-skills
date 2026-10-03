# DataHub ML Incident Response

Investigate ML data incidents with verified DataHub metadata and lineage, then prepare a safe, owner-ready remediation.

## What it does

1. Classifies six common ML incidents: freshness, feature desync, duplicate replay, partial backfill, late events, and stale lineage.
2. Verifies entity URNs, reads bounded downstream lineage, and enriches the graph with schema and ownership evidence.
3. Explains the specific model, feature, and transformation impact.
4. Produces remediation, validation, rollback, and a dry-run writeback payload.
5. Requires explicit human approval before it hands off a live write to DataHub Quality or Enrich.

## Usage

```text
/datahub-ml-incident-response payment authorizations are 132 minutes late
/datahub-ml-incident-response offline velocity is 18 but online is 7
/datahub-ml-incident-response the pipeline serves fraud_risk_v3 but the catalog says v2
```
