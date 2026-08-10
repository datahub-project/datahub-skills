---
name: datahub-ml-impact
description: |
  Use this skill when the user wants to understand how a dataset or column
  affects machine learning models - which models consume which features from a
  table, what breaks if a column is renamed, retyped or dropped, or which ML
  assets depend on a given data source. Use it for questions phrased around
  models, features, feature tables, training data or ML risk.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub ML Impact

Answers one question well: **which ML models consume which features from this data, and what
happens to them if it changes?**

This is narrower than general lineage on purpose. `/datahub-lineage` traverses everything downstream
of an entity and treats all consumers alike. This skill filters to the ML subgraph and reports at
feature granularity, because "three tables read this" and "this column is a named input to a model
serving live traffic" call for different responses.

## Boundaries

- General lineage traversal, or impact on tables and dashboards -> use `/datahub-lineage`.
- Finding an entity by name or description -> use `/datahub-search`.
- Editing tags, owners, or documentation -> use `/datahub-enrich`.
- Assertions and data quality -> use `/datahub-quality`.

Stay in this skill only while the question is about ML consumers.

## Step 1 - Identify the source entity

Accept a dataset URN directly. If given a name, resolve it first:

```bash
datahub get --urn "urn:li:dataset:(urn:li:dataPlatform:postgres,prod.features.user_features,PROD)"
```

If the user names a column rather than a table, keep the column - it narrows step 3.

Reject shell metacharacters in anything interpolated into a command.

## Step 2 - Find the ML entities downstream

DataHub models ML lineage natively, and the edges are not the same as dataset lineage:

| Edge                     | Aspect that creates it                |
| ------------------------ | ------------------------------------- |
| dataset -> feature       | `MLFeatureProperties.sources`         |
| feature -> feature table | `MLFeatureTableProperties.mlFeatures` |
| feature -> model         | `MLModelProperties.mlFeatures`        |
| model -> model group     | `MLModelProperties.groups`            |

So a model is typically **two hops** from the dataset that feeds it, with an `MLFeature` in between.
A one-hop query will find features and miss every model.

Traverse downstream with a depth of at least 2, then keep only `MLFEATURE`, `MLFEATURETABLE`,
`MLMODEL` and `MLMODELGROUP` results. See `references/graphql.md` for the query.

If the result set is empty, say so plainly: the dataset has no ML consumers recorded in DataHub. Do
not fall back to guessing from table names.

## Step 3 - Map columns to features

An `MLFeature`'s name is the feature name, which in most feature stores matches the source column.
Match the source dataset's `schemaMetadata.fields[].fieldPath` against the names of the `MLFeature`
entities found in step 2.

Report matches as **confirmed**. Report unmatched columns as **not known to be consumed** - never as
"unused". Without column-level lineage, absence of a match is weak evidence, and telling someone a
column is safe to drop on that basis is the failure mode this skill exists to prevent.

If the platform has column-level lineage, prefer it and say that you did.

## Step 4 - Report

Use `templates/impact-report.md`.

Order models by whether they are tagged production, then by how many of the changed columns they
consume. Always state:

- which models consume the entity, and through which features
- which specific columns each model depends on
- how many hops away each model is
- what evidence the mapping rests on (column lineage, or name matching)

When the user asked about a specific change (rename, type change, drop), close with the concrete
consequence for each model - which feature goes null, or which parse breaks - and stop there. Do not
recommend retraining or resolve anything on the user's behalf; this skill is decision support.

## Caveats to surface, not hide

- **Depth caps.** If traversal was capped, say the blast radius may be incomplete.
- **Feature stores that rename.** A feature named differently from its source column will not match
  by name. Say when the mapping is name-based.
- **Model freshness.** A model entity in DataHub is not proof it is deployed. If deployment status is
  unknown, say so rather than implying live traffic.
