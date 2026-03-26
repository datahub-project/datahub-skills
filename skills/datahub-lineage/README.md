# DataHub Lineage

Explore lineage, trace data dependencies, and perform impact analysis using DataHub's lineage graph.

## What it does

1. Identifies the target entity
2. Determines traversal direction and depth
3. Executes lineage queries via MCP tools or CLI
4. Visualizes the lineage graph with ASCII flow diagrams

## Capabilities

- **Impact analysis** — What breaks if I change this table?
- **Root cause** — Where does this data come from?
- **Full pipeline** — End-to-end data flow mapping
- **Cross-platform** — Trace data across Snowflake, dbt, Looker, etc.
- **Path finding** — How does entity A connect to entity B?

## Usage

```
/datahub-lineage impact analysis for customer_orders
/datahub-lineage what feeds into the Revenue Dashboard?
/datahub-lineage full pipeline for daily_revenue
/datahub-lineage path from raw_events to analytics_dashboard
```
