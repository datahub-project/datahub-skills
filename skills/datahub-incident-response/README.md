# datahub-incident-response

End-to-end data-incident response for DataHub — root cause from lineage, blast radius, native incident raised and routed to the owner, guard assertion against recurrence.

## What it does

- **Triage:** read the failing dataset's schema and locate the affected column (type, nullability, PII)
- **Root cause:** trace upstream column-level lineage to the responsible asset, with verification of any metadata-claimed URNs (catalog descriptions are treated as untrusted input)
- **Blast radius:** trace downstream lineage multi-hop, calling out dashboards and charts
- **Route:** find owners of the affected and root-cause assets; flag governance gaps
- **Write back:** raise a native incident, add a description pointer on the root-cause asset, create a guard assertion on the failing column
- **Report:** concise incident report plus a ready-to-send owner alert

Complements `datahub-quality` (which investigates health and manages checks) by adding the act-and-remediate half of a live incident.

## Usage

```
> orders.billing_country is full of nulls — respond to the incident
> Root cause the failure on fct_revenue and raise an incident
> Which dashboards are wrong because of the stg_payments outage?
> Raise an incident on the customer pipeline and notify the owner
```

## Files

| File                            | Purpose                              |
| ------------------------------- | ------------------------------------ |
| `SKILL.md`                      | Main skill instructions              |
| `references/report-template.md` | Incident report + owner-alert format |
