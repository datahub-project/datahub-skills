# The DataHub write surface

Every write Janus makes is idempotent and uses an OSS-native primitive. This is the exact
shape of each, verified against acryl-datahub 1.6.0.13 and a local GMS. The language model
never composes any of these payloads: it selects a fixed, parameterized function and supplies
validated arguments.

## Incidents

`raiseIncident` and `updateIncidentStatus` GraphQL mutations (no Python SDK wrapper exists).

```graphql
mutation {
  raiseIncident(
    input: {
      resourceUrn: "<urn>"
      type: FRESHNESS
      title: "..."
      description: "..."
    }
  )
} # returns the new incident urn
mutation {
  updateIncidentStatus(
    urn: "<incident urn>"
    input: { state: RESOLVED, message: "..." }
  )
}
```

- **Types:** `OPERATIONAL, FRESHNESS, VOLUME, FIELD, SQL, DATA_SCHEMA, CUSTOM`. There is no
  `COLUMN` type; the column-scoped one is `FIELD`. Read the allowed set from the installed
  `IncidentTypeClass`, never hardcode it.
- **An incident cannot attach to an mlModel.** `incidentInfo.entities` accepts only
  `dataset, chart, dashboard, dataFlow, dataJob, schemaField`; GMS answers a 500 for anything
  else. So a finding lands on the data asset it concerns (a leakage finding on the leaking
  `schemaField`, an upstream failure on the source `dataset`), and model-level risk is carried
  by structured properties instead.
- **Dedup** on `(resourceUrn, type, title)` over the resource's active incidents, found by
  traversing the `IncidentOn` relationship inbound (`graph.get_related_entities`). Do not read
  `incidentsSummary`: a Quickstart GMS never writes it, so a summary-based dedup finds nothing
  and duplicates every finding on every scan. `run_id` is provenance in the description, never
  part of the key.
- The **title is deterministic** and carries no measurement, because it is part of the dedup
  key: an LLM-reworded title would raise a duplicate every scan.

## Structured properties (model-level risk)

Emitted as aspects: the `StructuredPropertyDefinitionClass` on the property URN, then a
`StructuredPropertiesClass` assignment on the entity. Janus defines four on the mlModel:
`janus.trust_score` (number), `janus.trust_band` (string),
`janus.risk_flags` (multiple string), `janus.run_id` (string). A value is written
only when a detector computed it: no number is invented.

## Tags, terms, owners

The `model-at-risk` tag on each at-risk model, and a `leakage-risk` glossary term on a leaking
feature. There is no mlModel patch builder in `datahub.specific`, so these go through
read-merge-emit on the `globalTags` / `glossaryTerms` aspect. Never blind-write the aspect: it
is an upsert of the whole list and would drop tags or terms someone else applied.

## Guarding assertion

Rendered as open-assertions YAML and also emitted as an `assertionInfo` entity so it appears in
the Quality tab, plus an `assertionRunEvent` carrying the result Janus actually measured.

```yaml
version: 1
assertions:
  - entity: urn:li:dataset:(urn:li:dataPlatform:snowflake,ecommerce.public.loans_raw,PROD)
    type: freshness
    id_raw: janus.freshness.ecommerce.public.loans_raw # stable -> stable assertion guid
    lookback_interval: "6 hours"
    last_modified_field: updated_at
    schedule: { type: interval, interval: "6 hours" }
```

Three traps: `DataHubClient.assertions` is Cloud only (parse the YAML back through
`AssertionsConfigSpec` and emit `assertionInfo` yourself on OSS); never call
`get_assertion_info_aspect()`, which restamps `source.created` with now so the aspect never
converges; and `FixedIntervalFreshnessAssertion` reads `timedelta.seconds`, not
`total_seconds()`, so an SLA of a day or more is silently truncated (Janus refuses it).

## Documents (Model Impact Report)

A first-class `datahub.sdk.document.Document` entity linked to the model through
`related_assets`. The document id derives from the model, so it updates in place.

## ODCS input contract (optional extra)

For a model's input tables, an Open Data Contract Standard v3.1.0 YAML capturing the schema and
the freshness SLA Janus guards, validated with `datacontract-cli`. Read-and-render only;
it never mutates the graph, so it runs on a clean or dry-run scan
(`janus scan --model <m> --contract-out <path>`).

## Idempotency, in one line

Reruns never duplicate: incidents dedup on `(resourceUrn, type, title)`; the assertion URN is a
guid over the declaration; the document id derives from the model; structured properties and
labels are upserts. `run_id` is a description footer and a property, provenance not a key.
