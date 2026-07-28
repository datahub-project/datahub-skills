---
name: datahub-decision-governance
description: Govern operational decisions whose validity depends on DataHub context. Use when an agent must retrieve governed assets, schemas, lineage, ownership, or quality signals; produce an evidence-bound recommendation; require approval before action; save the approved result as a DataHub Document; compare changed evidence; or create a replacement decision without destroying prior history.
user-invocable: true
min-cli-version: 1.6.0
allowed-tools: Bash(datahub *)
---

# DataHub Decision Governance

Turn a recommendation into a reviewable, durable DataHub decision record whose
validity can be checked again when its evidence changes.

## Workflow

### 1. Resolve governed assets

1. Search DataHub for the relevant assets when URNs are not supplied.
2. Present ambiguous matches and require the user to choose.
3. Record the exact URNs. Do not substitute similarly named assets.

Use DataHub MCP tools where available:

- `search` to resolve assets.
- `get_entities` for descriptions, ownership, tags, terms, domains, and health.
- `list_schema_fields` for dataset fields.
- `get_lineage` for upstream sources and downstream consumers.
- `search_documents` for policies, runbooks, and prior governed knowledge.

### 2. Capture an evidence snapshot

Retrieve fresh context and retain:

- retrieval timestamp and tool names;
- full asset URNs;
- the context fields used by the decision;
- schema fields that affect the recommendation;
- relevant owners, governance classifications, and quality signals;
- upstream sources and downstream consumers;
- missing, unavailable, or truncated context.

Never silently replace a failed configured retrieval with fixture data. If a
fixture is explicitly requested, label it `deterministic_fixture`.

Read [references/decision-record-schema.md](references/decision-record-schema.md)
before creating the record.

### 3. Produce the recommendation

Run the domain analysis against the governed context. Preserve reproducible
artifacts when they exist:

- SQL or executable query;
- result columns and rows, or a content digest for large results;
- generated chart specification;
- model, agent, conversation, and tool-call identifiers;
- assumptions and warnings.

Separate retrieved evidence from agent interpretation. Do not claim that a
quality, ownership, or lineage signal exists when DataHub did not return it.

### 4. Calculate change and impact

When a prior decision exists:

1. Compare the complete prior and current evidence snapshots.
2. Highlight added, removed, and changed values.
3. Identify affected routines, pipelines, dashboards, owners, and approval
   policies using DataHub lineage and the decision's recorded dependencies.
4. Explain how each changed value affects the proposed action.
5. Keep the prior decision immutable.

Use
[templates/revalidation-report.template.md](templates/revalidation-report.template.md)
for the comparison.

### 5. Present the approval plan

Use [templates/decision-plan.template.md](templates/decision-plan.template.md).
Show:

- proposed action;
- evidence and context quality;
- governed dependencies;
- affected downstream consumers;
- previous versus updated values when applicable;
- exact DataHub write that will occur.

Obtain explicit approval before calling any mutation tool. Approval of a prior
revision does not approve a replacement.

### 6. Save and verify

After approval:

1. Call `save_document` with `document_type="Decision"`.
2. Include the recommendation, evidence, analysis artifacts, approval, and
   predecessor reference in the content.
3. Pass every governed dependency in `related_assets`.
4. Add narrow discovery topics such as `governed-decision` and the domain name.
5. Re-read the returned Document URN with `get_entities`.
6. Report the URN and verify the related assets.

If the write or read-back fails, preserve the approval and report a retryable
projection failure. Do not claim the decision is synchronized.

### 7. Revalidate instead of overwrite

When evidence changes:

1. Retrieve DataHub context again.
2. Re-run the analysis.
3. Create a new pending revision.
4. Link it to the prior decision as its predecessor or superseded record.
5. Require fresh approval.
6. Save a new DataHub Document only after approval.
7. Preserve access to both Documents and both evidence snapshots.

## Safety rules

- Treat DataHub as authoritative for catalog context, not for unstored agent
  assumptions.
- Require approval before every metadata mutation or operational action.
- Stop on the first write failure and report what succeeded.
- Never expose credentials, private reasoning, or unredacted sensitive rows.
- Prefer result digests or bounded samples when query results are large.
- Make fixture, live MCP, and recorded evidence visually distinguishable.
