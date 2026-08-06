# datahub-quality

Data quality management for DataHub — assertions, incidents, and notification subscriptions.

## What it does

- **Open Source:** Find assets with failing assertions or active incidents, inspect assertion results, check entity health status, and assess proof gaps for an exact proposed change
- **Cloud (Acryl SaaS):** Create and run assertions (freshness, volume, SQL, field, schema), set up smart/AI-inferred assertions, raise and resolve incidents, configure notification subscriptions via Slack, email, or Teams

## Usage

```
> Check quality of the orders table
> Show which impacted behaviors lack version-matched evidence for this schema change
> Find datasets with failing assertions
> Create a freshness assertion on my revenue table
> Subscribe me to assertion failures on orders via Slack
> Raise an incident on the customer pipeline
```

## Files

| File                                            | Purpose                                         |
| ----------------------------------------------- | ----------------------------------------------- |
| `SKILL.md`                                      | Main skill instructions                         |
| `references/assertion-mutations-reference.md`   | GraphQL mutations for all assertion types       |
| `references/incident-subscription-reference.md` | Incident and subscription mutations and queries |
| `references/change-proof-gap-reference.md`      | Version-bound evidence and proof-gap contract   |
| `templates/quality-report.template.md`          | Quality status report format                    |
| `templates/change-proof-gap-report.template.md` | Change evidence coverage report format          |
