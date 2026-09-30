# Triage report template

Fill in and present to the user. Lead with the answer, then the evidence chain.

```markdown
## Triage: <SYMPTOM_ASSET_NAME>

**Symptom:** <what the user observed — e.g. "daily summary is stale (last data 2016-03-01)">
**Root cause:** `<ROOT_CAUSE_STAGE>` — <one line: why this stage>
**Confidence:** <high | medium | low (data-level inference)>

### Evidence along the lineage

| Hop | Stage            | Signal (<freshness/volume/field/...>) | Verdict          |
| --- | ---------------- | ------------------------------------- | ---------------- |
| 0   | <symptom asset>  | <signal value>                        | carrying         |
| 1   | <stage>          | <signal value>                        | **BROKE HERE**   |
| 2   | <upstream stage> | <signal value>                        | healthy (source) |

**Why here:** <the boundary — this stage is unhealthy while its upstream is healthy>

**Suggested action:** <e.g. re-run the staging load from raw_trips>

**Incident:** <urn:li:incident:... raised on the symptom asset> (or "not raised — <reason>")

**Owners to notify:** <team(s) owning the root-cause stage>
```

## Notes

- If localization used the data-level fallback (metadata was clean), say so explicitly
  and mark confidence accordingly.
- For a fork, name only the signal relevant to this symptom; note the other downstreams
  were not affected by it.
- Keep it short. The value is the answer plus a legible evidence chain, not a wall of text.
