# DataHub Impact Gate

Decide whether a proposed schema or dbt change is safe to merge by computing its downstream blast radius onto ML models and dashboards, and returning a PASS / REVIEW / BLOCK recommendation.

## What it does

1. Identifies the changed dataset and classifies each field change (drop, rename, retype, add)
2. Resolves the downstream blast radius with a **skip-cache** lineage query
3. Walks the ML path `dataset → mlFeature → mlModel` and finds impacted dashboards
4. Resolves owners and existing guardrails for each impacted entity
5. Returns PASS / REVIEW / BLOCK with the impacted set — failing safe when lineage is ambiguous

## Capabilities

- **Merge decision** — Given a diff, is it safe to merge?
- **Blast radius** — Which ML models and dashboards depend on the changed fields?
- **Owner resolution** — Who needs to sign off or be notified?
- **Fail-safe verdicts** — A cached empty lineage answer never turns a breaking change into a PASS

## Usage

```
> Should I merge this? I'm dropping airport_fee from trip_features
> Impact gate for renaming pickup_ts on the trips table
> What breaks if I change the type of passenger_count to INT?
> /catalog-impact drop column fare_amount from raw_trips
```

## Files

| File                                       | Purpose                                                        |
| ------------------------------------------ | -------------------------------------------------------------- |
| `SKILL.md`                                 | Main skill instructions                                        |
| `commands/impact-gate.md`                  | One-shot "run the gate on this change" command                 |
| `references/ml-lineage-traversal.md`       | dataset → mlFeature → mlModel, cache and feature-table gotchas |
| `references/verdict-rubric.md`             | PASS / REVIEW / BLOCK criteria and fail-safe rules             |
| `templates/impact-gate-report.template.md` | Verdict report format                                          |
| `evaluations/*.json`                       | Behavioral test scenarios                                      |
