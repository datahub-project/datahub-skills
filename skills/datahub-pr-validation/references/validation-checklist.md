# PR Validation Checklist

Use this checklist when validating a PR against DataHub lineage.

## Pre-Validation

- [ ] Identify all entities affected by the change (datasets, models, dashboards)
- [ ] Search for URNs of affected entities: `datahub search "<name>" --where "entity_type = dataset" --limit 5`
- [ ] Confirm scope with user: "You're modifying X. I'll check what depends on these."

## Lineage Analysis

- [ ] Query downstream lineage (minimum 2 hops): `datahub lineage --urn "<URN>" --direction downstream --hops 2 --format json`
- [ ] Collect all affected URNs from results
- [ ] Check for direct consumers (1 hop): dashboards, views, other tables
- [ ] Check for indirect consumers (2 hops): derived tables, reports, exports
- [ ] Query upstream lineage if change may affect source data: `datahub lineage --urn "<URN>" --direction upstream --hops 1`

## Schema Change Analysis

If the change involves schema modifications:

- [ ] Check for column removals or renames → will break `SELECT col` downstream
- [ ] Check for type changes → will break joins/aggregations
- [ ] Check for new NOT NULL constraints → will break downstream inserts
- [ ] Check for column additions → safe for most, but check `SELECT *` consumers
- [ ] Verify no downstream models reference removed columns by name

## Ownership & Notification

- [ ] Batch-enrich affected entities with ownership: `datahub search "*" --where 'urn IN (...)' --projection "... ownership { owners { owner type } }"`
- [ ] Group owners by entity and impact level
- [ ] Build notification list with contact info (Slack channel, email)

## Risk Assessment

- [ ] Classify risk level: Critical / High / Medium / Low
- [ ] Critical: schema change affecting downstream with no migration
- [ ] High: logic change affecting data quality or new constraints
- [ ] Medium: backward-compatible changes (column addition)
- [ ] Low: documentation or naming changes only

## Reporting

- [ ] Generate PR validation report using template
- [ ] Include ASCII flow diagram for small impact graphs
- [ ] List all affected entities with owners and risk level
- [ ] Provide actionable next steps and migration recommendations
- [ ] Flag any lineage gaps (empty lineage for known important tables)

## Post-Validation

- [ ] Suggest column-level lineage check if schema changed
- [ ] Recommend quality assertions for critical downstream entities
- [ ] Suggest owner notification via `/datahub-enrich` if needed
