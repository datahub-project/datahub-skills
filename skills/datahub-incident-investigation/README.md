# datahub-incident-investigation

Lineage-driven root cause analysis for data incidents — from a reported symptom to a verified fix and a resolved incident.

## What it does

- **Frames the symptom** — pins down the affected field, the magnitude, and the onset before anything else
- **Localizes the fault** — walks upstream and column-level lineage to build a suspect set instead of guessing topology
- **Eliminates hypotheses** — every candidate must be necessary _and_ sufficient; magnitude and onset have to explain the symptom
- **Confirms with cited evidence** — a lineage path, quantitative proof naming the blamed field, and a competitor eliminated
- **Catches semantic failures** — value defects that pass every type, volume, freshness, and null threshold
- **Scopes and verifies the remediation** — right layer, minimal, no hidden rows, verified against the full suite
- **Writes the resolution back** — resolves the DataHub incident and attaches the RCA report

## Usage

```
> Revenue on the exec dashboard is 40x too high since last Tuesday — why?
> Investigate the active incident on the orders table
> Root cause analysis for the null spike in customer_email
> /catalog-investigate why did daily order counts drop on 2026-07-28
```

## Files

| File                                            | Purpose                                                          |
| ----------------------------------------------- | ---------------------------------------------------------------- |
| `SKILL.md`                                      | Main skill instructions                                          |
| `references/evidence-standards-reference.md`    | Evidence taxonomy, citation rules, necessity/sufficiency gate    |
| `references/investigation-recipes-reference.md` | GraphQL + CLI recipes for lineage, contracts, history, writeback |
| `templates/incident-rca-report.template.md`     | Postmortem report format                                         |
| `templates/hypothesis-ledger.template.md`       | Live hypothesis and evidence tracking table                      |
