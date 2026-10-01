# DataHub Learnings

Give agents shared long-term memory over the DataHub metadata graph: recall what previous agents learned about a dataset before acting on it, retain what you learned after.

## What it does

1. **Recall**: before touching a dataset, fetches the target entity plus one lineage hop upstream, reads any `io.datahub.agentMemory.learnings` structured-property values, and applies each one according to its confidence level.
2. **Retain**: after finishing a task, distills candidate learnings, checks them against the six write-time rules (no secrets, not schema-restating, deduped, honest confidence, never overwrite on contradiction, about the data not the task), and writes them back as a structured property plus a rendered documentation block.

## Capabilities

- **Semantic gotchas**: units, encodings, or scope that a column's name/type doesn't reveal ("`amount` is in cents").
- **Verified queries**: SQL patterns confirmed correct against ground truth, so the next agent doesn't re-derive them.
- **Join paths**: which key is actually safe to join on when more than one looks plausible.
- **Caveats**: quality or scope limitations that would mislead someone who didn't know them.
- **Metric definitions**: the agreed, verified definition of an ambiguous business metric.
- **Conflict handling**: a new observation that contradicts an existing learning is never silently applied over it; both are kept, both are surfaced.

## Usage

```
/datahub-learnings recall fct_orders before I query it
/datahub-learnings what do we know about dim_customers?
/datahub-learnings retain what I just learned about the June revenue query
```

Most of the time this skill runs implicitly: recall before the first query against a dataset in a session, retain after the task is done. See `SKILL.md`.

## Requires

- DataHub MCP server `mcp-server-datahub@0.6.0` (pinned to the verified version), launched with `TOOLS_IS_MUTATION_ENABLED=true`.
- The `io.datahub.agentMemory.learnings` structured property registered once per DataHub instance (script: https://github.com/ravadashreyas/Lore/blob/main/setup/register_properties.py).
- Full protocol definition: https://github.com/ravadashreyas/Lore/blob/main/protocol/SPEC.md.
