# ML Impact Analysis

## Proposed Change

**Entity:** <!-- dataset name and URN -->
**Scope:** <!-- whole dataset, or specific columns -->
**Change:** <!-- drop, rename, type change, semantic change, deprecation -->

## Impact Summary

**Features affected:** <!-- count -->
**Model versions affected:** <!-- count -->
**Model groups affected:** <!-- count -->
**Deployments affected:** <!-- count, or "none found / not ingested" -->
**Hops traced:** <!-- n -->

## Affected Models

<!-- Ordered by blast radius: deployed first, then latest versions, then superseded. -->

| Priority | Model group   | Version    | Deployed        | Latest          | Path to the change      | Owner          |
| -------- | ------------- | ---------- | --------------- | --------------- | ----------------------- | -------------- |
| 1        | <!-- name --> | <!-- v --> | <!-- yes/no --> | <!-- yes/no --> | <!-- feature or run --> | <!-- owner --> |

## Affected Features

| Feature       | Namespace   | Feature table  | Consuming models | Alternative source? |
| ------------- | ----------- | -------------- | ---------------- | ------------------- |
| <!-- name --> | <!-- ns --> | <!-- table --> | <!-- count -->   | <!-- yes/no -->     |

## Affected Training Pipelines

| Run or job    | Type                   | Last executed | Produces       |
| ------------- | ---------------------- | ------------- | -------------- |
| <!-- name --> | <!-- run / dataJob --> | <!-- date --> | <!-- model --> |

## Impact Graph

```text
<!-- e.g.

<dataset>.<column>
  ├─ DerivedFrom ← <feature>  (mlFeature)
  │    └─ Consumes ← <model> v7  [deployed]
  └─ Consumes ← <training run>
       └─ Produces → <model> v8  [latest]
-->
```

## Critical Findings

| Finding                                                 | Why it matters                             |
| ------------------------------------------------------- | ------------------------------------------ |
| <!-- e.g. single-source feature on a deployed model --> | <!-- no fallback if the column changes --> |

## Coverage Caveats

| Caveat                                       | Effect                                           |
| -------------------------------------------- | ------------------------------------------------ |
| <!-- e.g. no feature store ingested -->      | <!-- feature-level impact cannot be assessed --> |
| <!-- e.g. mlModelDeployment not ingested --> | <!-- deployment counts are a lower bound -->     |

## Recommendations

1. <!-- who to notify, with the owners resolved -->
2. <!-- retraining or migration sequence -->
3. <!-- assertions to add before the change lands -->
