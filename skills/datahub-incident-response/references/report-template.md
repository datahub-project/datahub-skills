# Incident Report: {incident_title}

**Affected asset:** `{affected_dataset_urn}`
**Affected column:** `{field_path}`
**Priority:** {priority}
**Native incident:** `{incident_urn}`

---

## Root Cause

**Asset:** {root_cause_name} (`{root_cause_urn}`)
**Column:** `{root_cause_field_path}`

{why — the lineage evidence: which upstream edge(s) implicate this asset, and how the
symptom on the affected column follows from it. Cite the traced path, e.g.
`raw_payments.country → stg_payments.billing_country → orders.billing_country`.}

---

## Blast Radius

**{total_count} downstream assets affected ({dashboard_chart_count} dashboards/charts).**

| Hop | Entity        | Type   | Platform   |
| --- | ------------- | ------ | ---------- |
| 1   | {entity_name} | {type} | {platform} |

Key dashboards/charts business users will see:

- {dashboard_name} ({platform})

---

## Owner

Routed to: **{owner_name}** ({ownership_type}, {person_or_group}) — owner of {root_cause_or_affected_asset}.

{Governance gaps, if any: assets in this incident with no owner assigned.}

---

## Writes Performed

| Write               | Target                   | Result            |
| ------------------- | ------------------------ | ----------------- |
| Native incident     | `{affected_dataset_urn}` | `{incident_urn}`  |
| Description pointer | `{root_cause_urn}`       | appended          |
| Guard assertion     | `{field_path}`           | `{assertion_urn}` |

---

## Suggested Fix

{Concrete next step for an engineer on the root-cause asset, e.g. "Backfill
`stg_payments.billing_country` from `raw_payments.country` for partitions since
2026-07-20, then re-run the orders build. The new guard assertion
(`{field_path} IS NOT NULL`) will confirm the fix."}

---

### 📨 Alert to owner

```text
To: {owner_name}
Priority: {priority}

{affected_dataset_name}.{field_path} is failing: {one_line_symptom}.

Root cause: {root_cause_name}.{root_cause_field_path} ({one_line_evidence}).
Blast radius: {total_count} downstream assets, including {key_dashboards}.

Suggested fix: {one_line_fix}.

Tracking: native DataHub incident {incident_urn} (see the Incidents tab on
{affected_dataset_name}). A guard assertion now watches {field_path} for recurrence.
```
