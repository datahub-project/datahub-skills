# datahub-ml-lineage

Investigate ML model and feature problems with DataHub metadata — trace a model version through its training runs, features, and upstream datasets, or trace a data change forward to the models it affects.

## What it does

1. Confirms ML metadata is actually ingested, and says so when it is not
2. Resolves whether the subject is a model group, a model version, or a deployment
3. Traverses the ML graph: model → training run → input datasets, and model → features → source datasets
4. Compares training runs — metrics, hyperparameters, input sets — before implicating the data
5. Follows column-level lineage to the **source** column and compares dataset profiles across the run window
6. Reports the evidence chain, the hypotheses ruled out, and the gaps that bound the conclusion

## Capabilities

- **Regression triage** — why is this version worse than the last one?
- **Version comparison** — what differs between two model versions and their runs?
- **Provenance audit** — what produced this model, and could it be reproduced?
- **Feature root cause** — which feature degraded, and where did the values stop being real?
- **ML impact analysis** — which models, features, and deployments does this table or column feed?
- **Training / serving divergence** — is the serving data the same data the model trained on?

## Usage

```text
/datahub-ml-lineage why did fraud_detector v7 regress?
/datahub-ml-lineage compare fraud_detector v6 and v7
/datahub-ml-lineage what trained customer_churn v3?
/datahub-ml-lineage which models use analytics.customer_features?
/datahub-ml-lineage impact of dropping raw.crm.customers.age on our models
```

## Files

| File                                        | Purpose                                                      |
| ------------------------------------------- | ------------------------------------------------------------ |
| `SKILL.md`                                  | Main skill instructions                                      |
| `references/ml-entity-model-reference.md`   | ML entity types, URNs, aspects, relationships, GraphQL paths |
| `references/ml-investigation-patterns.md`   | Traversal recipes, hypothesis discipline, stop conditions    |
| `templates/model-investigation.template.md` | Regression and provenance findings report                    |
| `templates/ml-impact-analysis.template.md`  | Downstream ML impact report                                  |

## Notes

- Requires ML metadata from an ML source (MLflow, SageMaker, Vertex AI, Databricks, Feast, or a custom emitter). Coverage differs by source — see the entity model reference.
- Some fields this skill needs (`mlTrainingRunProperties`, `datasetProfiles`, the raw `deployments` list) are only reachable via `datahub graphql` or `datahub get`, so it uses MCP tools and the CLI together.
