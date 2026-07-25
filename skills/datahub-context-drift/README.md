# DataHub Context Drift

Find documentation that has stopped being true — not documentation that is missing.

## What it does

1. Reads the description a human actually sees (editableProperties first, then properties)
2. Compares what it claims against the schema and lineage
3. Reports drift with the evidence, and abstains when it cannot substantiate a claim
4. Drafts a correction and waits for your approval
5. Writes back, then reads back to confirm the value landed

```
> /datahub-context-drift check the descriptions in the finance domain
> /datahub-context-drift is this table's description still accurate?
> /datahub-context-drift the trip_records column was renamed, what else is stale?
```

All writes require your explicit approval for that specific text.

## Why this is not a coverage check

In February 2023 the NYC TLC renamed `airport_fee` to `Airport_fee` in its public
trip records. One letter, no error, no announcement. The description stayed as it
was and quietly stopped being true.

Coverage tooling scores that table perfectly: the description exists, the columns
are documented, nothing is missing. For "what has not been written yet", use
`/datahub-audit`. This skill reads what _has_ been written.
