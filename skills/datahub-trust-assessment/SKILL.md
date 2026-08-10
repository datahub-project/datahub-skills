# DataHub Trust Assessment Skill

Provides a detailed framework and execution workflows for assessing, scoring, and remediating data trust dimensions across metadata assets indexed in DataHub.

## Description
This skill enables agents and platform systems to continuous audit metadata catalogs, compute five-dimension trust scores, propagate cascade risks downstream, generate code remediations (dbt tests, SQL assertions, and data contracts), and gate machine learning pipelines before training executions.

## Prerequisites
- DataHub GMS connection URL (default: `http://localhost:8080`)
- Google Gemini API Key configured in environment as `PRAXIS_GOOGLE_API_KEY`
- Read/Write credentials to target metadata databases

---

## Trust Dimensions Table

| Dimension | Weight | Audit Scope | Deductions |
|---|---|---|---|
| **Provenance** | 25% | Documentation, Owners, Domains, Glossary | -10 for missing owner, -15 for missing description |
| **Integrity** | 30% | Assertions, fresh events, deprecation states | -10 for failed assertion, -30 for deprecation status |
| **Stability** | 15% | Primary keys, nullable field patterns, schemas | -10 for missing PK, -15 for volatile nullable shifts |
| **Lineage** | 15% | Upstream and downstream connectivity factors | -10 for missing upstream lineage connections |
| **Adoption** | 15% | Usage query volumes, unique active users | -15 for zero queries in previous 30 days |

---

## DataHub Tools Integration

### Metadata Read Queries
1. **Search Entity Count:** Query catalog inventory stats.
2. **Get Entity Metadata:** Extract schema fields, documentation, ownership, and glossary mappings.
3. **Get Lineage:** Retrieve active upstream and downstream lineage connections.
4. **Get Dataset Queries:** Query usage statistics and user frequencies.

### Metadata Writeback Actions
1. **Add Tags:** Add `praxis-trusted`, `praxis-review`, or `praxis-untrusted` tags based on final scores.
2. **Add Structured Properties:** Write composite scores and grade indicators directly to target assets.
3. **Update Description:** Augment schema documentation with generated findings.
4. **Save Document:** Mutate DataHub knowledge base posts to publish Daily Digests.

---

## Execution Workflows

### 1. Full Catalog Assessment Run
Scans all datasets, calculates scores, cascades penalties downstream, generates contracts for low-trust nodes, opens PRs, and writes reports back to DataHub.
```bash
$env:PYTHONPATH="src"
.venv\Scripts\python.exe -m praxis.api.main
```

### 2. Single Asset Audit View
Evaluates trust dimensions for a single target URN.
```graphql
query getDatasetTrust($urn: String!) {
  dataset(urn: $urn) {
    customProperties {
      key
      value
    }
  }
}
```

### 3. ML Training Data Ingestion Gate
Checks target dataset safety before running model training pipelines.
```bash
curl -X POST http://localhost:8000/api/ml/check-training-data \
  -H "Content-Type: application/json" \
  -d '{"source_urns": ["urn:li:dataset:(urn:li:dataPlatform:hive,logging_events,PROD)"]}'
```

Add datahub-trust-assessment skill for continuous catalog trust scoring
