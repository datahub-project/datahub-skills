# ML Entity Model Reference

DataHub's ML metadata model, as it matters for lineage traversal and investigation. Verified against the entity registry and `datahub-graphql-core` schema on `master`.

---

## Entity Types

| Entity                | Search filter value   | Represents                                                     | Key properties aspect                                       |
| --------------------- | --------------------- | -------------------------------------------------------------- | ----------------------------------------------------------- |
| `mlModelGroup`        | `mlModelGroup`        | A registered model — the container for all of its versions     | `mlModelGroupProperties`                                    |
| `mlModel`             | `mlModel`             | One model version, with its own metrics and hyperparameters    | `mlModelProperties`                                         |
| `mlModelDeployment`   | `mlModelDeployment`   | A running deployment of a model                                | `mlModelDeploymentProperties`                               |
| `dataProcessInstance` | `dataProcessInstance` | One execution — a training run when subtyped `ML Training Run` | `dataProcessInstanceProperties` + `mlTrainingRunProperties` |
| `container`           | `container`           | An experiment, project, or workspace grouping runs             | `containerProperties`                                       |
| `mlFeatureTable`      | `mlFeatureTable`      | A feature table / feature view in a feature store              | `mlFeatureTableProperties`                                  |
| `mlFeature`           | `mlFeature`           | One feature — the unit a model consumes                        | `mlFeatureProperties`                                       |
| `mlPrimaryKey`        | `mlPrimaryKey`        | The entity key a feature table is keyed by                     | `mlPrimaryKeyProperties`                                    |
| `versionSet`          | `versionSet`          | Groups versioned assets (model versions, dataset versions)     | `versionSetProperties`                                      |

Entity type filter values are camelCase entity names; the CLI converts them to the GraphQL `EntityType` enum. `mlModel` → `MLMODEL`, `mlModelGroup` → `MLMODEL_GROUP`, `mlFeature` → `MLFEATURE`, `mlFeatureTable` → `MLFEATURE_TABLE`, `dataProcessInstance` → `DATA_PROCESS_INSTANCE`.

---

## URN Formats

```text
mlModelGroup:        urn:li:mlModelGroup:(urn:li:dataPlatform:PLATFORM,NAME,ENV)
mlModel:             urn:li:mlModel:(urn:li:dataPlatform:PLATFORM,NAME,ENV)
mlModelDeployment:   urn:li:mlModelDeployment:(urn:li:dataPlatform:PLATFORM,NAME,ENV)
mlFeatureTable:      urn:li:mlFeatureTable:(urn:li:dataPlatform:PLATFORM,NAME)
mlFeature:           urn:li:mlFeature:(FEATURE_NAMESPACE,NAME)
mlPrimaryKey:        urn:li:mlPrimaryKey:(FEATURE_NAMESPACE,NAME)
dataProcessInstance: urn:li:dataProcessInstance:GUID
container:           urn:li:container:GUID
versionSet:          urn:li:versionSet:(ID,ENTITY_TYPE)
```

Note the asymmetries: `mlFeature` and `mlPrimaryKey` are keyed by feature namespace rather than platform and carry no environment, and `mlFeatureTable` has no environment either. Do not assume a dataset-shaped three-part URN for every ML entity.

Model version naming is source-specific. The MLflow source builds the version URN as `<registered_model_name><separator><version>` (separator configurable), so a group named `fraud_detector` with version `7` becomes `fraud_detector_7`. Never parse a version number out of a name — read `properties.version` or `versionProperties.version.versionTag`.

---

## Subtypes

Runs and experiments are ordinary entities distinguished by the `subTypes` aspect. Filter with `entity_subtype`, which maps to the indexed `typeNames` field, and use the **display string**, not the enum constant name:

| Concept              | Entity                | `entity_subtype` value |
| -------------------- | --------------------- | ---------------------- |
| MLflow training run  | `dataProcessInstance` | `ML Training Run`      |
| MLflow experiment    | `container`           | `ML Experiment`        |
| Vertex AI experiment | `container`           | `Experiment`           |
| Vertex AI run        | `dataProcessInstance` | `Experiment Run`       |

```bash
datahub search "*" --where "entity_type = dataProcessInstance AND entity_subtype = 'ML Training Run'" --limit 20
```

---

## Relationships

These are the graph edge names. Use them with `relationships(input: { types: [...], direction: ... })`; the ones marked as lineage edges also appear in `datahub lineage` and `get_lineage` output.

| Edge name     | From aspect                                          | From → To                                             | Lineage |
| ------------- | ---------------------------------------------------- | ----------------------------------------------------- | ------- |
| `MemberOf`    | `mlModelProperties.groups`                           | mlModel → mlModelGroup                                | Yes     |
| `TrainedBy`   | `mlModelLineageInfo.trainingJobs`                    | mlModel / mlModelGroup → dataJob, dataProcessInstance | Yes     |
| `UsedBy`      | `mlModelLineageInfo.downstreamJobs`                  | mlModel / mlModelGroup → dataJob, dataProcessInstance | Yes     |
| `Consumes`    | `mlModelProperties.mlFeatures`                       | mlModel → mlFeature                                   | Yes     |
| `Consumes`    | `dataProcessInstanceInput.inputs`                    | dataProcessInstance → dataset                         | Yes     |
| `Produces`    | `dataProcessInstanceOutput.outputs`                  | dataProcessInstance → dataset, mlModel                | Yes     |
| `DeployedTo`  | `mlModelProperties.deployments`                      | mlModel → mlModelDeployment                           | No      |
| `DerivedFrom` | `mlFeatureProperties.sources`                        | mlFeature → dataset                                   | Yes     |
| `Contains`    | `mlFeatureTableProperties.mlFeatures`                | mlFeatureTable → mlFeature                            | No      |
| `KeyedBy`     | `mlFeatureTableProperties.mlPrimaryKeys`             | mlFeatureTable → mlPrimaryKey                         | No      |
| `InstanceOf`  | `dataProcessInstanceRelationships.parentTemplate`    | dataProcessInstance → dataJob, dataFlow               | No      |
| `ChildOf`     | `dataProcessInstanceRelationships.parentInstance`    | dataProcessInstance → dataProcessInstance             | No      |
| `UpstreamOf`  | `dataProcessInstanceRelationships.upstreamInstances` | dataProcessInstance → dataProcessInstance             | Yes     |

`Consumes` and `Produces` are each emitted from two different aspects, so filter on the entity type of the result when a query could return both features and datasets. The edge-based variants `DataProcessInstanceConsumes` and `DataProcessInstanceProduces` exist for the `inputEdges` / `outputEdges` forms of the same aspects; query both names when a source populates the edge form.

Direction to use, given the entity you start from:

| Question                               | Start at              | Types         | Direction  |
| -------------------------------------- | --------------------- | ------------- | ---------- |
| Which versions are in this group?      | `mlModelGroup`        | `MemberOf`    | `INCOMING` |
| Which run trained this version?        | `mlModel`             | `TrainedBy`   | `OUTGOING` |
| Which models did this run produce?     | `dataProcessInstance` | `Produces`    | `OUTGOING` |
| What did this run read?                | `dataProcessInstance` | `Consumes`    | `OUTGOING` |
| Which models consume this feature?     | `mlFeature`           | `Consumes`    | `INCOMING` |
| Which features come from this dataset? | `dataset`             | `DerivedFrom` | `INCOMING` |
| Which runs read this dataset?          | `dataset`             | `Consumes`    | `INCOMING` |
| Which table holds this feature?        | `mlFeature`           | `Contains`    | `INCOMING` |

---

## GraphQL Field Paths

Aspect names and GraphQL field names differ. These are the paths that matter, with the traps called out.

| What you want                   | GraphQL path                                                                                                                                                                                |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Model version label             | `mlModel.properties.version` (a `String`)                                                                                                                                                   |
| Model hyperparameters           | `mlModel.properties.hyperParams { name value }`                                                                                                                                             |
| Model training metrics          | `mlModel.properties.trainingMetrics { name value }`                                                                                                                                         |
| Model's training runs           | `mlModel.properties.mlModelLineageInfo.trainingJobs`                                                                                                                                        |
| Model's downstream jobs         | `mlModel.properties.mlModelLineageInfo.downstreamJobs`                                                                                                                                      |
| Model's features                | `mlModel.properties.mlFeatures` (URN **strings**)                                                                                                                                           |
| Model's groups                  | `mlModel.properties.groups { urn name }`                                                                                                                                                    |
| Version position                | `mlModel.versionProperties { isLatest version { versionTag } versionSet { urn latestVersion { urn } } }`                                                                                    |
| Run metrics and hyperparameters | `dataProcessInstance.mlTrainingRunProperties { id outputUrls hyperParams { name value } trainingMetrics { name value } }`                                                                   |
| Run outcome                     | `dataProcessInstance.state(limit: 1) { status timestampMillis durationMillis result { resultType nativeResultType } }`                                                                      |
| Run's experiment                | `dataProcessInstance.container { urn properties { name } }`                                                                                                                                 |
| Run subtype                     | `dataProcessInstance.subTypes { typeNames }`                                                                                                                                                |
| Feature's source datasets       | `mlFeature.properties.sources { urn properties { name } platform { name } }`                                                                                                                |
| Feature table contents          | `mlFeatureTable.properties { mlFeatures { urn name } mlPrimaryKeys { urn name } }`                                                                                                          |
| Column statistics over time     | `dataset.datasetProfiles(startTimeMillis:, endTimeMillis:, limit:) { timestampMillis rowCount fieldProfiles { fieldPath nullCount nullProportion uniqueCount min max mean median stdev } }` |
| Version list for a version set  | `versionSet(urn:) { latestVersion { urn } versionsSearch(input: { query: "*" }) { ... } }`                                                                                                  |

**Traps:**

- `trainingJobs` and `downstreamJobs` are **not** flat fields on `properties`. They sit inside `mlModelLineageInfo`, added by a schema extension to both `MLModelProperties` and `MLModelGroupProperties`. `properties { trainingJobs }` fails with `FieldUndefined`.
- `mlModelProperties.deployments` has **no GraphQL equivalent**, and `mlModelDeployment` has no GraphQL type at all. Read it from the raw aspect: `datahub get --urn "<MLMODEL_URN>" --aspect mlModelProperties`.
- `MLModelGroup` has no `models` field. List versions through the `MemberOf` relationship or a filtered search, not a nested selection.
- `mlFeatures` returns URN strings while `mlFeatureTableProperties.mlFeatures` returns objects. The asymmetry is real; batch-resolve the string form.
- `MLFeature.featureProperties` and `MLFeatureTable.featureTableProperties` are deprecated aliases of `properties`. Use `properties`.
- `MLMetric` and `MLHyperParam` both expose `value` as a `String`. Cast before comparing numerically.

When in doubt, introspect instead of guessing:

```bash
datahub graphql --describe MLModel --recurse --format json
datahub graphql --describe dataProcessInstance --recurse --format json
```

---

## Aspects Worth Knowing

| Aspect                        | On                    | Contents                                                                                                                  |
| ----------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `mlModelProperties`           | `mlModel`             | version, type, hyperParams, trainingMetrics, onlineMetrics, mlFeatures, groups, deployments, trainingJobs, downstreamJobs |
| `mlModelGroupProperties`      | `mlModelGroup`        | name, description, version, trainingJobs, downstreamJobs                                                                  |
| `mlTrainingRunProperties`     | `dataProcessInstance` | run id, outputUrls, hyperParams, trainingMetrics                                                                          |
| `dataProcessInstanceInput`    | `dataProcessInstance` | `inputs` / `inputEdges` — what the run read                                                                               |
| `dataProcessInstanceOutput`   | `dataProcessInstance` | `outputs` / `outputEdges` — what the run produced                                                                         |
| `dataProcessInstanceRunEvent` | `dataProcessInstance` | timeseries run state and result                                                                                           |
| `mlModelTrainingData`         | `mlModel`             | Model-card training datasets, with motivation and preprocessing text                                                      |
| `mlModelEvaluationData`       | `mlModel`             | Model-card evaluation datasets                                                                                            |
| `mlModelMetrics`              | `mlModel`             | Model-card performance measures and decision thresholds                                                                   |
| `intendedUse`                 | `mlModel`             | Primary uses, users, out-of-scope uses                                                                                    |
| `versionProperties`           | `mlModel`             | version tag, aliases, `isLatest`, version set                                                                             |
| `datasetProfile`              | `dataset`             | Timeseries row counts and per-column statistics                                                                           |

The model-card aspects (`mlModelTrainingData`, `mlModelEvaluationData`, `mlModelMetrics`, `intendedUse`, `mlModelEthicalConsiderations`, `mlModelCaveatsAndRecommendations`) are populated by hand or by custom emitters far more often than by ingestion sources. Treat their absence as a documentation gap, not a lineage gap.

---

## What Each Source Actually Emits

Coverage varies sharply. Check what you have before designing a traversal.

| Source             | Groups & versions | Training runs | Run → dataset inputs                  | Features            |
| ------------------ | ----------------- | ------------- | ------------------------------------- | ------------------- |
| MLflow             | Yes               | Yes           | Only if the run logged dataset inputs | No                  |
| SageMaker          | Yes               | Yes (jobs)    | Yes                                   | Yes (Feature Store) |
| Vertex AI          | Yes               | Yes           | Partial                               | No                  |
| Databricks / Unity | Yes               | Partial       | Partial                               | No                  |
| Feast              | No                | No            | n/a                                   | Yes                 |

**MLflow specifics**, since it is the most common source:

- The run's `container` is the experiment; `properties.created.time` is the MLflow run start time.
- `mlModelProperties.hyperParams` and `trainingMetrics` are **copied from the run** onto the version, so model-level and run-level values are duplicates for MLflow but not for other sources.
- Logged datasets are ingested as **platform-local dataset references** on the `mlflow` platform, whose single upstream is the real warehouse or storage table with edge type `COPY`. A run's `Consumes` edge therefore lands on a stub; keep going upstream until the platform is a real store.
- Models registered without a run have no `trainingJobs`, no hyperparameters, and no metrics. This is common in migrated registries.

---

## Related Documentation

- DataHub ML entity docs: <https://docs.datahub.com/docs/generated/metamodel/entities/mlmodel>
- MCP server tool list: <https://docs.datahub.com/docs/features/feature-guides/mcp>
- ML platform ingestion standards: `standards/source_types/ml_platforms.md`
