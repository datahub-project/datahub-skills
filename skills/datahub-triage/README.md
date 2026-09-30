# datahub-triage

On-call incident triage for DataHub. Takes a symptom on a downstream asset and
localizes it to the upstream stage where it originated, then opens an incident.

Where `datahub-lineage` traces dependencies and `datahub-quality` checks a known
asset's health, `datahub-triage` does the on-call loop that neither covers on its
own: **symptom → walk lineage → compare health signals stage by stage → pinpoint the
break → write the finding back as an incident.**

The key idea: a downstream symptom is usually propagation, not origin. Freshness lag
and quality defects flow downstream unchanged, so the root cause is the most upstream
stage that is already unhealthy while its own upstream is still healthy.

```
> Why is the revenue dashboard stale?
> Triage the nulls in the billing mart
> /datahub-triage the daily summary is empty — find where it broke
```

See `SKILL.md` for the full workflow.
