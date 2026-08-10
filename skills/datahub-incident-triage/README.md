# DataHub Incident Triage

Triage a data incident end to end: recall prior post-mortems, trace column-level lineage to a root cause, rank downstream blast radius, coordinate approved metadata actions, and write the post-mortem back to DataHub.

## What it does

1. Resolves the failing entity and validates the signal from `Dataset.health`
2. Recalls prior post-mortems on the dataset and its ancestors before any traversal
3. Walks upstream one hop at a time and stops only on an intrinsically broken node
4. Ranks downstream impact with measured usage, then resolves owners in a batch
5. Proposes writes (incident, tags, notifications), executes only after approval, and verifies each artifact
6. Stores a structured post-mortem so the next incident on the same path is cheaper

## Capabilities

- **Root-cause stop rule:** a node is the cause only when it is unhealthy and none of its own upstreams is
- **Column-level tracing:** follows the fields implicated by the assertion or freshness signal
- **Blast radius:** datasets, charts, dashboards, data jobs, and ML assets, deduplicated and ranked by usage
- **Durable memory:** a searchable structured property, plus a Document narrative where supported
- **Open Source aware:** reads assertion detail through GraphQL, since `get_dataset_assertions` is Cloud-only

## Usage

```
/datahub-incident-triage triage the failing assertion on daily_revenue
/datahub-incident-triage why is customer_orders stale?
/datahub-incident-triage what is the blast radius of raw_events?
/datahub-incident-triage write a post-mortem for the revenue pipeline outage
```

Or ask naturally: "find the root cause of this freshness breach", "who should be paged for the orders pipeline?".
