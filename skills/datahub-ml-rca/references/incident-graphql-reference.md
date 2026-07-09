# Incident GraphQL reference (verified against DataHub OSS v1.5)

All shapes below were verified by schema introspection and live execution
against a self-hosted DataHub v1.5.0.6. They also work on DataHub Cloud.

## Raise an incident

```bash
datahub graphql --query 'mutation { raiseIncident(input: {
  resourceUrn: "<DATASET_URN>",
  type: FRESHNESS,
  title: "staging_trips stopped 9 days behind raw_trips",
  description: "Root cause of degraded model <MODEL_URN>. Evidence: ...",
  priority: CRITICAL
}) }'
```

Returns the new incident URN as a string.

### Field notes (pitfalls verified the hard way)

- `type` is an `IncidentType` enum: `FRESHNESS`, `VOLUME`, `FIELD`, `SQL`,
  `DATA_SCHEMA`, `OPERATIONAL`, `CUSTOM`. **The value for column-level issues
  is `FIELD`** — some older docs say `COLUMN`, which does not exist in the
  schema.
- `priority` is an `IncidentPriority` enum (`LOW`, `MEDIUM`, `HIGH`,
  `CRITICAL`), not a number.
- `customType` (string) is required when `type: CUSTOM`.
- Optional: `startedAt` (epoch millis), `assigneeUrns` (corpuser/corpGroup
  urns), `resourceUrns` (raise one incident across multiple assets).
- **Supported resource types are server-dependent.** Datasets, dashboards,
  charts, dataFlows, and dataJobs work broadly; OSS v1.5 rejects `mlModel`
  resource urns (the mutation fails with a GraphQL error). If you need to
  flag a model, raise the incident on its root-cause dataset and tag the
  model instead.

## List incidents on an entity

```bash
datahub graphql --query '{ dataset(urn: "<DATASET_URN>") {
  incidents(state: ACTIVE, start: 0, count: 20) {
    total
    incidents { urn incidentType title description priority
                status: incidentStatus { state stage message } }
  }
} }'
```

- `state` filter: `ACTIVE` or `RESOLVED`; omit for all.
- Incident listing is served from the search index — allow a few seconds of
  eventual consistency after raising before you expect the new incident to
  appear in the list.

## Update / resolve an incident

```bash
datahub graphql --query 'mutation { updateIncidentStatus(
  urn: "<INCIDENT_URN>",
  input: { state: RESOLVED, stage: FIXED, message: "Backfill completed." }
) }'
```

- **The input type is `IncidentStatusInput`.** The schema also contains an
  `UpdateIncidentStatusInput` type — it is a decoy; using it in a variable
  declaration fails with `VariableTypeMismatch`.
- `stage` values: `TRIAGE`, `INVESTIGATION`, `WORK_IN_PROGRESS`, `FIXED`,
  `NO_ACTION_REQUIRED`.

## MCP alternative

If the environment uses the DataHub MCP server instead of the CLI, the same
operations are available as the `get_incidents`, `raise_incident`, and
`update_incident_status` tools (added in
[mcp-server-datahub#137](https://github.com/acryldata/mcp-server-datahub/pull/137);
requires `TOOLS_IS_MUTATION_ENABLED=true` and
`DATA_QUALITY_TOOLS_ENABLED=true`).
