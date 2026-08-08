# DataHub tools used by datahub-ml-guardian

The skill uses the DataHub CLI (`datahub …`) and/or the DataHub MCP server
(`uvx mcp-server-datahub@latest`). Mutations require `TOOLS_IS_MUTATION_ENABLED=true`.
Tool names + argument shapes below were pinned from the MCP server's live `list_tools()`.

## Read — trace the blast radius

| Tool                                                | Purpose                                                                  |
| --------------------------------------------------- | ------------------------------------------------------------------------ |
| `search`                                            | Resolve a changed table/column name to its dataset URN                   |
| `list_schema_fields`                                | Confirm the column and read the real schema before generating a fix      |
| `get_lineage` (`urn`, `upstream: bool`, `max_hops`) | Walk downstream to features, models, deployments                         |
| `get_lineage_paths_between`                         | Prove the exact path `dataset → mlFeature → mlModel`                     |
| `get_entities`                                      | Read `mlModelProperties` (trainingMetrics, deployments) for the baseline |

## Write — contribute back to the graph

| Tool                 | Signature                                                                                                                                   | Purpose                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `add_tags`           | `entity_urns[]`, `tag_urns[]`                                                                                                               | Flag the at-risk model (`urn:li:tag:at-risk`, `urn:li:tag:ml-guardian`)                 |
| `remove_tags`        | `entity_urns[]`, `tag_urns[]`                                                                                                               | Clear the flags (reset)                                                                 |
| `add_owners`         | `entity_urns[]`, `owner_urns[]`, `ownership_type`                                                                                           | Route to the responsible team / data steward                                            |
| `remove_owners`      | `entity_urns[]`, `owner_urns[]`                                                                                                             | Undo ownership (reset)                                                                  |
| `update_description` | `entity_urn`, `operation` ∈ `replace`/`append`/`remove`, `description`                                                                      | Add a visible at-risk banner to the model                                               |
| `save_document`      | `document_type` ∈ `Insight`/`Decision`/`FAQ`/`Analysis`/`Summary`/`Recommendation`/`Note`/`Context`, `title`, `content`, `related_assets[]` | Record the incident (root cause + blast radius + metric delta) as a knowledge-base note |

## Notes

- **`add_tags` / `add_owners` validate that the referenced tag / corpuser urn already
  exists** — create the tag and agent-user entities first (e.g. via the SDK: `TagProperties`,
  `CorpUserInfo`) or the mutation is rejected.
- The OSS MCP server does **not** expose a lifecycle/deprecation tool or a native-incident
  tool. For a native `Deprecation` banner or a native `Incident` entity, emit those aspects
  via the DataHub Python SDK / CLI (`DeprecationClass`, `IncidentInfoClass`).
- Prefer proposals over direct mutations where a governance/approval workflow exists — keep a
  human in the loop for deprecation.
- Every mutation should be traceable: include the full lineage path and the measured metric
  delta (e.g. AUC delta) in the incident document.
