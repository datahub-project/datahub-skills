---
name: datahub-change-preflight
description: Analyzes proposed schema or structural changes against DataHub metadata (lineage, assertions, domains) to construct a Preflight Safety Case Document.
author: datahub-project
tags:
  - governance
  - ci-cd
  - agent
---

# DataHub Change Preflight Skill

This skill equips agents with the ability to act as automated PR reviewers or CI/CD preflight checks.
It leverages the DataHub SDK to:
1. Fetch downstreams (lineage) of an asset that is about to change.
2. Evaluate potential breaking changes (e.g., dropping a column used by a dashboard).
3. Generate a "Safety Case" summarizing the risk.
4. Write the Safety Case back to DataHub natively using Context Documents (`datahub.sdk.document.Document`).

## Instructions for Agents

When requested to perform a preflight check or evaluate a schema change:
1. Identify the DataHub URN of the asset being modified.
2. Use `DataHubGraph` to retrieve the asset's schema and downstream lineage.
3. Identify semantic breaks (e.g., removing a field, changing a type) and map them to downstream impacts.
4. Construct a Markdown summary of your findings (the "Safety Case").
5. Save the Safety Case to DataHub by invoking `Document.create_document(...)` and linking it to the asset via `add_related_asset(urn)`.

## Example Usage (Python)

```python
from datahub.ingestion.graph.client import get_default_graph
from datahub.sdk.document import Document

def run_preflight_skill(graph, dataset_urn: str, proposed_change: str, run_id: str):
    # Agent evaluates the change...
    risk_level = "HIGH"
    analysis_text = f"# Safety Case for {dataset_urn}\n\nRisk: {risk_level}\n\nProposed Change: {proposed_change}"
    
    # Save natively as a Document
    doc_id = f"safety-case-{run_id}"
    doc = Document.create_document(
        id=doc_id,
        title=f"Preflight Check: {run_id}",
        text=analysis_text,
        subtype="Safety Case",
        show_in_global_context=False
    )
    doc.add_related_asset(dataset_urn)

    for mcp in doc.generate_mcp():
        graph.emit(mcp)
        
    return f"urn:li:document:{doc_id}"
```
