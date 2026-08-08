# Document tool reference

The document tools exposed by the DataHub MCP server and the Agent Context Kit.

## Availability

| Requirement     | Detail                                                    |
| --------------- | --------------------------------------------------------- |
| Server version  | `mcp-server-datahub` v0.5.0+                              |
| DataHub version | Cloud 0.3.16+ **or** Core 1.4.0+                          |
| Mutations       | `save_document` requires `TOOLS_IS_MUTATION_ENABLED=true` |

The read tools `search_documents` and `grep_documents` are **automatically hidden when the
catalog contains no documents**. Their absence means an empty knowledge base, not a
misconfiguration. `save_document` is not hidden this way, so capture works on a fresh
instance.

Verified against the MCP server source: `save_document` carries
`@min_version(cloud="0.3.16", oss="1.4.0")`, and the hide-list is
`DOCUMENT_TOOL_NAMES = frozenset({"search_documents", "grep_documents"})`.

## Tools

### `search_documents`

Keyword search across documents, with filters for platforms, domains, tags, glossary terms
and owners. Use first, in recall mode.

### `grep_documents`

Regex search _within_ document content. Use when the user's phrasing is specific enough that
a keyword search would over-match — a policy name, an error string, a column name.

### `save_document`

Saves a standalone document (insight, decision, FAQ, runbook). Documents are organised under
a parent folder.

Relevant environment variables:

| Variable                              | Default  | Effect                                      |
| ------------------------------------- | -------- | ------------------------------------------- |
| `SAVE_DOCUMENT_TOOL_ENABLED`          | `true`   | Enables the tool                            |
| `SAVE_DOCUMENT_PARENT_TITLE`          | `Shared` | Parent folder for saved documents           |
| `SAVE_DOCUMENT_ORGANIZE_BY_USER`      | `false`  | Nest saved documents per user               |
| `SAVE_DOCUMENT_RESTRICT_UPDATES`      | `true`   | Only allow updates inside the shared folder |
| `DATAHUB_MCP_DOCUMENT_TOOLS_DISABLED` | `false`  | Disable document read tools entirely        |

## Verifying a write

Do not rely on the model's own account of what it did. Confirm a `save_document` call
appears in the tool-call stream before reporting success, and surface a clear failure if it
does not. The common causes of a missing write are mutations being disabled, a token without
write permission, and a DataHub version below the minimum above.

## Via the Agent Context Kit

When building a custom agent rather than using an MCP client, the same tools arrive through
the kit:

```python
from datahub.sdk.main_client import DataHubClient
from datahub_agent_context.google_adk_tools import build_google_adk_tools

client = DataHubClient(server=gms_url, token=gms_token)
tools = build_google_adk_tools(client, include_mutations=True)  # includes save_document
```

With `include_mutations=True` the kit exposes 12 mutation tools including `save_document`;
with it `False`, 10 read tools. Note that the glossary mutation is named
`add_glossary_terms` (not `add_terms`).

Do not call `build_google_adk_cloud_tools` against DataHub Core — those tools are Cloud-only.
