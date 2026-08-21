# Evidence-Provenance Emission Reference

How to register an evidence set with full chain-of-custody lineage using the
`acryl-datahub` Python SDK. MCP mutation tools can tag and describe existing
entities, but they cannot **create** Datasets, DataJobs, or lineage edges —
that requires SDK emission against GMS.

## Entities per finding

| Entity   | Purpose                               | Key aspects                              |
| -------- | ------------------------------------- | ---------------------------------------- |
| Dataset  | The materialized evidence table       | schema, description, tags, custom props  |
| DataFlow | The investigation (one per case)      | name, description                        |
| DataJob  | One hunt run within the investigation | verbatim SQL in properties, input/output |

## Minimal emission pattern

```python
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.mce_builder import (
    make_data_flow_urn, make_data_job_urn, make_dataset_urn, make_tag_urn)
from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.metadata.schema_classes import (
    DataJobInfoClass, DataJobInputOutputClass, DatasetPropertiesClass,
    GlobalTagsClass, TagAssociationClass)

graph = DataHubGraph(DatahubClientConfig(server="http://localhost:8080"))

evidence = make_dataset_urn("duckdb", "warehouse.analytics.hunt_result", "PROD")
sources = [make_dataset_urn("duckdb", f"warehouse.staging.{t}", "PROD")
           for t in ("emails", "recipients")]

flow = make_data_flow_urn("investigation", "case_001", "PROD")
job = make_data_job_urn("investigation", "case_001", "hunt_leakage")

aspects = [
    (evidence, DatasetPropertiesClass(
        name="hunt_result",
        description="Hypothesis, method, thresholds go here.",
        customProperties={"hunt": "leakage", "run_at": "..."})),
    (evidence, GlobalTagsClass(tags=[
        TagAssociationClass(tag=make_tag_urn("evidence")),
        TagAssociationClass(tag=make_tag_urn("pending-review"))])),
    (job, DataJobInfoClass(
        name="hunt_leakage", type="SQL",
        customProperties={"sql": VERBATIM_SQL})),
    (job, DataJobInputOutputClass(
        inputDatasets=sources, outputDatasets=[evidence])),
]
for urn, aspect in aspects:
    graph.emit_mcp(MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect))
```

`DataJobInputOutputClass` is what makes the lineage walkable in the UI:
evidence dataset → lineage tab → the DataJob (SQL visible in properties) →
each source table.

## Review-state transitions

Reviews swap tags and stamp an audit trail into custom properties:

```python
# confirmed | rejected replaces pending-review
props.customProperties.update({
    "review_verdict": "confirmed",
    "reviewed_by": reviewer,          # real identity, not the agent
    "reviewed_at": timestamp,
    "review_note": note,
})
```

Keep the transition atomic from the reviewer's perspective: tag swap and
property stamp in the same review action.

## Metadata-derived evidence

When a finding comes from graph traversal (ownership, lineage gaps) rather
than warehouse SQL, materialize it anyway — render the derived rows as
`SELECT * FROM (VALUES ...) AS t(cols...)` and store that as the DataJob's
SQL. Reproducibility should not depend on whether the source was a table or
the metadata graph itself.

## Gotchas observed in the field

- Glossary term URNs may carry a node prefix (`Taxonomy.Term`); strip both
  the URN prefix and the node path when matching short names, or materiality
  flags silently zero out.
- The OSS quickstart runs with metadata-service auth off — no token needed
  locally, but hosted instances need a PAT in `DATAHUB_GMS_TOKEN`.
- `DataHubGraph` is itself an emitter; no separate `DatahubRestEmitter`
  needed when you already hold a graph client.
