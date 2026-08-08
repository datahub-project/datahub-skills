# DataHub tools used by datahub-lifecycle

The skill uses the DataHub CLI (`datahub …`) and/or the DataHub MCP server
(`uvx mcp-server-datahub@latest`). Mutations require `TOOLS_IS_MUTATION_ENABLED=true`.
Tool names + argument shapes below were pinned from the MCP server's live `list_tools()`.

## Read — find candidates and check the blast radius

| Tool                                                | Purpose                                                             |
| --------------------------------------------------- | ------------------------------------------------------------------- |
| `search`                                            | Find candidates by name/stem; resolve a name to its dataset URN     |
| `get_dataset_queries`                               | See whether (and how) the asset is still queried — the usage signal |
| `get_lineage` (`urn`, `upstream: bool`, `max_hops`) | Enumerate downstream consumers before retiring                      |
| `get_entities`                                      | Read owners / description / existing deprecation state              |
| `list_schema_fields`                                | Confirm the asset and compare against a proposed replacement        |

## Write — deprecate, notify, record

| Tool                 | Signature                                                                                                                                   | Purpose                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `update_description` | `entity_urn`, `operation` ∈ `replace`/`append`/`remove`, `description`                                                                      | Append a visible sunset banner + link to the replacement     |
| `add_owners`         | `entity_urns[]`, `owner_urns[]`, `ownership_type`                                                                                           | Make sure someone owns the sunset                            |
| `save_document`      | `document_type` ∈ `Insight`/`Decision`/`FAQ`/`Analysis`/`Summary`/`Recommendation`/`Note`/`Context`, `title`, `content`, `related_assets[]` | Record the retirement decision (reason, replacement, cutoff) |

## Notes

- **The OSS MCP server does not expose a lifecycle/deprecation tool.** Set the native
  `Deprecation` aspect (with a note and a decommission date) via the DataHub CLI / Python SDK
  (`DeprecationClass`); use `update_description` for the human-visible banner in the meantime.
- `add_owners` validates that the referenced corpuser/group urn already exists — create it
  first if needed.
- Use `document_type="Decision"` for the sunset record so it reads as a governance decision,
  not a generic note.
- Prefer proposals over direct mutations where a governance/approval workflow exists — leave
  the final deprecation to an owner.
- A retirement decision must cite evidence: the query count from `get_dataset_queries` and the
  consumer count from `get_lineage`.
