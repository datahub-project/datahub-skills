# ML Platforms Sources

**Source Type:** API-Based

## Overview

ML platforms like MLflow, Weights & Biases, SageMaker, and Vertex AI expose model and experiment metadata through REST APIs.

## What to Extract

- **MLModelGroup** - Model registries and model groups
- **MLModel** - Individual model versions
- **MLFeatureTable** - Feature stores (SageMaker Feature Store, Feast)
- **MLFeature** - Individual features in feature tables
- **Containers** - Experiments, projects, workspaces
- **DataProcessInstance** - Training runs and experiments
- **Tags** - Model and experiment tags
- **Lineage** - Model → Training data relationships

## Required Aspects for ML Models

| Aspect                   | Required              | Description                                                  |
| ------------------------ | --------------------- | ------------------------------------------------------------ |
| `dataPlatformInstance`   | ✅ ALWAYS             | Links entity to data platform. **Always required.**          |
| `mlModelProperties`      | ✅ ALWAYS             | Model metadata (name, description, version, hyperparameters) |
| `mlModelGroupProperties` | ✅ IF MODEL GROUP     | Model group/registry metadata                                |
| `ownership`              | ✅ IF SOURCE PROVIDES | Model owners (required if source exposes owners)             |
| `globalTags`             | ✅ IF SOURCE PROVIDES | Tags from source system                                      |
| `container`              | ✅ IF HIERARCHICAL    | Links to parent container (experiment, project)              |
| `status`                 | 🔄 AUTO               | Auto-generated for all entities                              |

## Required Aspects for Feature Tables

| Aspect                     | Required              | Description                                         |
| -------------------------- | --------------------- | --------------------------------------------------- |
| `dataPlatformInstance`     | ✅ ALWAYS             | Links entity to data platform. **Always required.** |
| `mlFeatureTableProperties` | ✅ ALWAYS             | Feature table metadata                              |
| `mlFeatureProperties`      | ✅ FOR FEATURES       | Individual feature metadata                         |
| `upstreamLineage`          | ✅ IF SOURCE PROVIDES | Link to source datasets                             |
| `status`                   | 🔄 AUTO               | Auto-generated for all entities                     |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details

## Special Considerations

- **Model Versioning**: Track model versions and their relationships
- **Feature Store Integration**: Link features to their source datasets via `upstreamLineage`
- **Experiment Tracking**: Capture training runs and metrics
- **Training Data Lineage**: Connect models to training datasets

## Example Sources in DataHub

- `src/datahub/ingestion/source/mlflow.py`
- `src/datahub/ingestion/source/sagemaker/`
