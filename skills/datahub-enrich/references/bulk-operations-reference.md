# Bulk Operations Reference

## Batch-First Approach

Use batch mutations (`batchAddTags`, `batchAddTerms`, `batchAddOwners`, `batchSetDomain`, `batchUpdateDeprecation`, `batchSetDataProduct`) for all operations where they exist — they work for single and multi-entity use cases.

For operations without batch support (`updateDescription`, `upsertStructuredProperties`), execute sequentially after user confirmation.

## Workflow: Search → Plan → Approve → Execute

1. **Search** — find target entities with `datahub search` and appropriate filters
2. **Plan** — show matched entities (up to 20) and proposed changes
3. **Approve** — get explicit user confirmation with total entity count
4. **Execute** — run batch mutations; for sequential operations, report progress every 10 entities
5. **Report** — success/failure summary

## Safety Limits

| Limit | Value |
| --- | --- |
| Preview | Show up to 20 entities |
| Auto-proceed | Up to 50 entities with confirmation |
| Hard limit | None (user can override, but always confirm count) |
| Error tolerance | Stop on first error |

## Error Handling

1. Stop immediately on error
2. Report what succeeded and what failed
3. Ask: skip and continue, or abort?

## Rollback

DataHub has no built-in rollback. For safety:

- Show before/after in the enrichment plan so values can be restored manually
- Include undo mutations in the enrichment report (e.g., the inverse `batchRemoveTags` call)
- For descriptions, note the original text so it can be re-applied
