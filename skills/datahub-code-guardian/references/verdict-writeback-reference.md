# Verdict writeback reference

How to record what a run concluded, in the two shapes DataHub already keeps. Both operations work on DataHub Core.

## Assertion identity

Derive the assertion URN from the check and the asset, never from the run.

```
urn:li:assertion:<tool>-<check>-<short-digest-of-asset-urn>
```

A caller-chosen URN passed as the `urn` argument of `upsertCustomAssertion` is what makes a second run land on the same assertion instead of creating a duplicate. Server-assigned identity, a timestamp in the URN, or a digest of the finding text all produce a pile of one-run assertions and no timeline, which is the same as recording nothing.

Keep the digest short and stable. A truncated SHA of the asset URN is enough, since collisions inside one tool's namespace are the only thing that matters.

## Registering the assertion

```graphql
mutation UpsertAssertion(
  $assertion: String!
  $entity: String!
  $category: String!
  $description: String!
  $platform: String!
  $externalUrl: String!
) {
  upsertCustomAssertion(
    urn: $assertion
    input: {
      entityUrn: $entity
      type: $category
      description: $description
      platform: { name: $platform }
      externalUrl: $externalUrl
    }
  ) {
    urn
  }
}
```

`type` is the free-text category shown beside the assertion, and the assertion's own type becomes `CUSTOM`. `platform` names the tool the assertion is attributed to, which is what lets a reader tell one tool's verdicts from another's. `description` should start with the check identifier and then say what the check measures, so the timeline is readable in the UI without opening the report.

## Reporting a result

One result per run, against the assertion registered above.

```graphql
mutation ReportResult(
  $assertion: String!
  $timestampMillis: Long!
  $type: AssertionResultType!
  $properties: [StringMapEntryInput!]
  $externalUrl: String!
) {
  reportAssertionResult(
    urn: $assertion
    result: {
      timestampMillis: $timestampMillis
      type: $type
      properties: $properties
      externalUrl: $externalUrl
    }
  )
}
```

`type` is `SUCCESS`, `FAILURE`, or `ERROR`. Use `ERROR` when the check could not answer, and never as a synonym for a failing check, because a reader treats the two completely differently.

`properties` comes back as `result.nativeResults` on the read, keyed exactly as it was sent.

## Properties to record

| Key           | Value                                                                  |
| ------------- | ---------------------------------------------------------------------- |
| `rule`        | The check identifier, stable across runs                               |
| `measurement` | The measured value and the allowed one, for example `3 (allowed <= 0)` |
| `findings`    | How many findings this run reported                                    |
| `repair`      | `offered`, `previewed`, `applied`, or `refused`                        |
| `reasons`     | The first few finding messages, joined, so the next reader sees why    |
| `reasoning`   | A model's stated reasoning, only when the check was a judgment         |
| `confidence`  | That model's confidence as a unit fraction, alongside `reasoning`      |

Drop empty keys rather than sending blanks. Keep each value short, since this is a summary a later agent reads in bulk, not the report itself.

## The human receipt

Beside the machine timeline, point each judged asset at the run that judged it.

```graphql
mutation AttachReport($urn: String!, $url: String!, $label: String!) {
  addLink(input: { resourceUrn: $urn, linkUrl: $url, label: $label })
}
```

Institutional memory is additive and editable, so a link states what a tool found beside whatever a person wrote. **Never reach for `updateDescription` to leave a note.** A description is usually a sentence a person wrote, and an agent that overwrites it destroys the context the next reader needs. If the description is genuinely wrong, that is an `/datahub-enrich` conversation with a human in it.

## Rules for the writeback step

- **Record passes as well as failures.** A check that stopped failing is the most valuable line in the timeline, and it exists only if passes are recorded.
- **One record per check and asset pair**, not one per finding. Findings belong in `reasons`.
- **Never write as a side effect of a read.** Recording is a separate step behind an explicit flag, setting, or user approval.
- **Ask before writing.** Show how many assertions and results will be created, and against which assets. Confirm the count explicitly above 20 assets.
- **Do not re-analyse to record.** Project the report the run already produced. Recording that recomputes anything can disagree with what the user was shown, which makes the timeline untrustworthy.

## Verifying the write

Re-read the asset's assertions after writing and confirm the count did not double. A second assertion with the same description and a different URN means the identity is not stable, and the timeline will never accumulate.
