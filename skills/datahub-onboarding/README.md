# datahub-onboarding

Onboard new data-team members and capture departing members' knowledge as living,
catalog-validated documents in DataHub.

## What it does

1. Orients a new team member in an unfamiliar catalog: maps the domain, works out which of
   the same-named copies of a table is the canonical one, flags deprecated tables (and names
   their replacements from the deprecation note), identifies the actual owners and the
   escalation contact to talk to, and surfaces glossary definitions and real recorded
   queries.
2. Builds a "week one" learning path for a specific role and domain, grounded in the
   catalog's own certification, ownership and health metadata, and saves it back to DataHub
   as a document linked to the datasets it covers.
3. Captures a departing member's task knowledge as a runbook. Every step carries a dataset
   URN, an action and the _why_, enriched from the live catalog with owners, schema, real
   SQL and lineage, then saved back to DataHub.
4. Re-validates any runbook or onboarding document on read-back with deterministic checks
   (columns still exist, dataset not deprecated since, health not failing, owners unchanged)
   and warns before anyone follows a stale step. Each claim is pinned to the version of the
   catalog aspect it was checked against, so a verdict can be reproduced rather than trusted.
5. Writes the staleness back as state a person will walk into: a `StaleRunbook` tag, the
   status and the specific breaking change as structured properties, an assertion that fails
   while the runbook is stale, and an incident assigned to whoever owns the dataset today.
6. Proposes the correction the catalog supports — the renamed column, the replacement named
   in a deprecation note, the current owner — as a diff for a human to approve, and names
   what it deliberately did not correct.

## Capabilities

- Canonical-copy disambiguation from certification markers, ownership coverage, usage tags
  and lineage position (`search`, `get_entities`), rather than "the table with the
  best-sounding name"
- Deprecation and health guardrails read off the entity's `deprecation` and `health` fields,
  with the replacement named from the deprecation note
- Owner, escalation-contact and glossary-term discovery (`get_entities`, including
  `structuredProperties`) for people, SLAs and vocabulary
- Real recorded SQL (`get_dataset_queries`), never invented queries, and an explicit "no
  recorded queries" when the catalog has none
- Runbook enrichment with schema, ownership, and one-hop lineage (`get_lineage`)
- Write-back to the catalog (`save_document`) linked to referenced datasets, reporting the
  document URN
- Deterministic staleness detection on every document read-back, per claim rather than per
  document, each pinned to a recomputable fingerprint of the aspect it depends on
- Staleness written back as catalog state: tag, structured properties, a runbook-validity
  assertion, and an incident assigned to the dataset's current owner
- Catalog-derived corrections proposed as a reviewable diff, with the evidence for each edit
  and an explicit list of what needs a person instead
- `datahub` CLI fallback when the MCP server is unavailable, including
  `datasetUsageStatistics` for raw query volume, which no MCP tool currently exposes

## Usage

```text
/catalog-onboarding analytics engineer joining the revenue domain
/catalog-onboarding build a week-one learning path for a data scientist on the growth team
/catalog-onboarding capture Dana's monthly revenue close process as a runbook before she leaves
/catalog-onboarding is the "Monthly Revenue Close" runbook still accurate?
/catalog-onboarding the revenue close runbook is stale — record it in the catalog and show me the fix
```
