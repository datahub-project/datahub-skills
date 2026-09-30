---
name: datahub-semantic-conflicts
description: |
  Use this skill to investigate inconsistent KPIs, find conflicting SQL definitions of the same business metric in DataHub, prove their impact, recommend a canonical definition, and detect future semantic drift. Triggers on conflicting revenue, active-user, conversion, or other metric definitions.
user-invocable: true
allowed-tools: Bash(metricguard *)
---

# DataHub Semantic Conflicts

Investigate competing metric definitions from DataHub, use deterministic SQL
analysis and warehouse execution for facts, and keep every mutation behind human
approval.

## Operating contract

- Start from DataHub metadata, not local example files.
- Use DataHub MCP `search`, `get_dataset_queries`, `get_entities`, and
  `get_lineage` for graph facts.
- Use MetricGuard for SQL signatures, semantic diffs, clustering, divergence,
  staged resolution, and drift checks.
- Never ask an LLM to calculate semantic equivalence or numeric divergence.
- Treat canonical selection as a recommendation until a human approves it.
- Never call DataHub mutation tools directly. Stage validated proposals and
  report their exact status.

## Prerequisites

Confirm:

1. `metricguard --help` succeeds.
2. DataHub MCP connectivity is configured and `metricguard datahub tools`
   exposes search, entity, query, and lineage tools.
3. A warehouse connection is optional. Without it, report semantic conflicts
   but do not claim numeric impact.

If MetricGuard is unavailable, gather candidates and provenance with DataHub,
but stop before claiming semantic equivalence, divergence, or a resolved
canonical. Explain that deterministic verification is missing.

## Workflow

### 1. Define the investigation scope

Extract a short metric label such as `weekly revenue` or `weekly active users`.
Reject shell metacharacters before putting user text in a CLI command. Prefer a
narrow metric label over a full-catalog `*` scan.

### 2. Run the graph-native agent

Use one explicit goal containing the metric, warehouse result columns, and
action boundary:

```bash
metricguard agent \
  "Investigate conflicting definitions of <metric> from DataHub. Use graph \
  ownership, domains, tags, and lineage. Quantify the most decision-relevant \
  pair with key_col=<time-column> and value_col=<metric-column>. Recommend a \
  canonical only from graph and warehouse facts, then invoke the resolution \
  tool using the exact metric_family returned by DataHub."
```

The agent must:

1. Search DataHub and retrieve observed SQL.
2. Batch-fetch entity context and trace upstream and downstream lineage.
3. Extract deterministic semantic signatures.
4. Cluster likely implementations into metric families.
5. Compare every relevant pair and classify changed dimensions.
6. Execute the highest-value pair when the warehouse is connected.
7. Recommend a canonical using visible evidence and explicit inference.
8. Stage the validated resolution package or report that it already exists.

### 3. Inspect the durable audit trail

```bash
metricguard runs list
metricguard runs show <run-id>
```

Verify the trace contains the investigation, selected warehouse proof,
resolution result, and final answer. Treat the action tool result—not the prose
summary—as authoritative.

### 4. Apply the human decision

If new proposals were staged:

```bash
metricguard proposals list
metricguard proposals show <proposal-id>
metricguard proposals approve <proposal-id>
```

Approval writes the decision document, canonical semantic-signature structured
properties, canonical/divergent tags, and warning redirects through the gated
DataHub client. Do not approve on the user's behalf.

If the action result says `human_approval_required: false`, state that the
equivalent resolution is already executed. Do not tell the user to approve it
again.

### 5. Guard future SQL

Use the canonical signature governed in DataHub as the contract:

```bash
metricguard guard datahub-check '<canonical-dataset-urn>' path/to/change.sql
```

Interpret exit codes exactly:

- `0`: no semantic drift
- `1`: semantic break
- `2`: no canonical graph contract

## Required report

Keep the final report concise and include:

1. Metric family and competing DataHub assets.
2. Exact changed semantic dimensions and severities.
3. Numeric mean, maximum, and first divergence when executed.
4. Graph evidence: owners, domains, tags, and lineage.
5. Canonical recommendation, separating facts from inference.
6. Exact action status, proposal IDs, and whether approval remains.
7. Run ID for the durable audit trace.

## Grounding rules

- Do not claim an asset is certified, peer-reviewed, version-controlled,
  popular, compliant, or authoritative unless DataHub returned that fact.
- Do not invent proposal IDs or shorten URNs.
- Copy `metric_family` exactly from DataHub. The staging tool rejects mismatches.
- A zero-edge lineage response means no lineage was returned; it does not prove
  there are no dependencies.
- Do not describe staged proposals as executed.
- Do not describe executed proposals as pending approval.
- If the model narrative conflicts with the tool trace, report the tool trace.
