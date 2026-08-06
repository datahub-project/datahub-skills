# DataHub ML Lineage

Trace lineage past the warehouse boundary — from columns, through features and feature tables,
to models and the endpoints serving them.

## What it does

1. Identifies the model, feature or endpoint the question is really about
2. Walks the chain: `FineGrainedLineage` → `MLFeatureProperties.sources` → `MLFeatureTableProperties` → `MLModelProperties` → deployments
3. Resolves features to specific columns, and states how confidently
4. Reports the path, and the deployment status that decides whether it matters

## Capabilities

- **What feeds this model** — the columns behind a model, not just the feature table
- **What breaks if I change this column** — filtered to the ML consumers that fail silently
- **Label leakage** — is a feature derived from the thing being predicted?
- **Offline vs online** — do the training and serving definitions of a feature still agree?
- **Restricted data** — does a PII-classified column reach a deployed model?

## Usage

```
/datahub-ml-lineage what data feeds churn_propensity_v7?
/datahub-ml-lineage does segment_churn_rate leak the label?
/datahub-ml-lineage what models break if I change raw_orders.amount?
```

## Not this skill

Lineage that stays between datasets, dashboards and charts is `/datahub-lineage`. This one is
for questions whose subject is a **model, a feature or an endpoint**, where the warehouse is
only the first half of the path.

## The two traps

**The granularity break.** `MLFeatureProperties.sources` points at _datasets_;
`FineGrainedLineage` operates on _columns_. Nothing in the open-source model joins them, so an
agent that keeps reasoning at column level past that boundary is inventing precision the graph
does not have. The skill resolves it in tiers — declared, name match, dataset-wide — and says
which tier the answer rests on.

**Features are not their names.** The same logical feature usually exists twice, offline and
online, in different tables. Comparing paths by node identity therefore reports every feature
as divergent. Compare the ordered chain of transform operations instead, and ignore
value-preserving hops.
