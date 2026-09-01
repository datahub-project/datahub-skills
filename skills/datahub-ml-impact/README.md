# datahub-ml-impact

Assess the ML impact of a data change using the DataHub context graph: walk
column-level lineage from a changed dataset to every affected feature, model,
and deployment; score severity P0–P3; and check features for **structural
target leakage** (from lineage + captured SQL alone — no data access).

## Example prompts

- "Which models are affected by the schema change on `raw_transactions`?"
- "What's the blast radius of dropping `amount_usd`?"
- "Is it safe to retrain `fraud_model` right now?"
- "Check `fraud_model` for target leakage."

## What it adds over the existing skills

The registry covers setup, search, lineage, enrichment, and quality — none of
it ML-aware. This skill layers an ML interpretation on top of the same MCP
tools: feature/model/deployment resolution, a severity rubric keyed to
deployment status, and three structural leakage rules (direct label lineage,
post-outcome assets, forward-looking SQL windows).

Developed and tested against DataHub v1.6.0 (OSS quickstart) with the
MLflow + dbt connectors, as part of the Blast Radius agent
(github.com/Danishlynx/blast-radius).

The write-back step raises incidents directly on the affected `mlModel`,
`mlFeature`, or `mlFeatureTable`, which needs a build carrying the ML
incident support merged into datahub-project/datahub after v1.7.0
(PRs 19112, 19132 and 19367). On older releases the skill falls back to an
incident on the upstream dataset.
