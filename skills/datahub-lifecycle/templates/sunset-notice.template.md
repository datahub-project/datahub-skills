# Sunset: `{{ asset }}`

**Status:** deprecated · **Decommission date:** {{ cutoff_date }}
**Decided by:** {{ owner }}

## Why

{{ reason }}

## Replacement

Use `{{ replacement }}` instead. {{ replacement_notes }}

## Evidence

- Recent queries: {{ query_count }} (from `get_dataset_queries`)
- Downstream consumers: {{ consumer_count }} (from `get_lineage`)

## Consumers to migrate

{{ consumers_list }}

<!--
Filled in by the skill and saved back via save_document (document_type="Decision"). Keep the
evidence (query + consumer counts) and the replacement pointer so the retirement is auditable
and reversible. Remove the asset only once lineage is empty and queries have stopped.
-->
