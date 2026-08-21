# Authority boundaries — Incident Gate

## Two approvals

| Approval       | Authorizes                                      | Does not authorize                       |
| -------------- | ----------------------------------------------- | ---------------------------------------- |
| Trust ALLOW    | Offering a scoped mutation plan to a human      | Executing any mutation                   |
| HITL `approve` | Exactly the actions + URNs in the approved plan | Scope changes, new tags, extra documents |

Chat phrases like “looks good” or “go” are **not** HITL approve unless the user explicitly confirms the listed actions.

## Two sessions

| Session | Mutations | Purpose                                                            |
| ------- | --------- | ------------------------------------------------------------------ |
| Write   | Enabled   | Apply approved `add_tags` / `save_document` / `update_description` |
| Verify  | Disabled  | Fresh re-read; prove durability                                    |

Never verify with the same mutation-enabled session as the write. Recreate the client/tools with `include_mutations=False` (Agent Context Kit) or an MCP config without mutation tools.

## Evidence that may block

- Failing / erroring assertion run results from `get_dataset_assertions`
- Missing ownership when the plan would mutate production assets
- Missing lineage when blast cannot be computed for a high-severity signal
- Tool / GMS errors (`GRAPH_UNAVAILABLE`) — fail closed, do not invent context

## What DataHub does and does not do

DataHub stores metadata and governance evidence. Incident Gate writes tags/documents/description notes so the **next person or agent inherits context**. It does not repair warehouse data, restart pipelines, or delete source records.
