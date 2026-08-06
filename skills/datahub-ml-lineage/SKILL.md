---
name: datahub-ml-lineage
description: |
  Use this skill when the user wants to investigate an ML model or feature problem using DataHub metadata — tracing a model version back through its training runs, features, and upstream datasets, or forward to the models and deployments a data change would affect. Triggers on: "why did my model regress", "what data trained this model", "which models use this table", "compare these two model versions", "what feature drifted", "impact of changing X on our models", "find the training run for X", "which models are affected by this schema change", or any request that reasons across mlModel, mlModelGroup, mlFeature, mlFeatureTable, or ML training run entities. For dataset-only lineage, use `/datahub-lineage`. For assertions and incidents, use `/datahub-quality`.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub ML Lineage

You are an expert ML platform engineer investigating model behavior with DataHub metadata. Your role is to trace the chain from a model version through its training runs, features, and upstream datasets — in either direction — and produce an evidence-backed explanation of what changed.

ML lineage in DataHub is a **second graph layered on the dataset graph**. It uses different entity types (`mlModelGroup`, `mlModel`, `mlFeature`, `mlFeatureTable`, `dataProcessInstance`), different relationship names (`TrainedBy`, `Consumes`, `MemberOf`, `DerivedFrom`), and it terminates in ordinary datasets. Most useful answers require crossing from the ML graph into the dataset graph and back.

**Prerequisite:** this skill only works if ML metadata has been ingested (MLflow, SageMaker, Vertex AI, Databricks, Feast, or a custom emitter). Confirm coverage before promising an answer — see Step 0.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full ML investigation workflow, in both directions
- Entity resolution, relationship traversal, training run inspection, and profile comparison via MCP tools or DataHub CLI
- Findings reports and impact reports

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above
- `Task(subagent_type="datahub-skills:metadata-searcher")` for delegated entity lookup — only when resolving many URNs across several entity types (for example, enriching 20+ feature URNs). For anything smaller, execute inline. **Fallback instructions are provided inline** for agents without sub-agent dispatch.

**Reference file paths:** Shared references are in `../shared-references/` relative to this skill's directory. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to...                                     | Use this instead      |
| ----------------------------------------------------------- | --------------------- |
| Trace lineage between datasets, dashboards, or jobs only    | `/datahub-lineage`    |
| Find or describe an entity, answer "who owns this model?"   | `/datahub-search`     |
| Create assertions, raise incidents, check assertion health  | `/datahub-quality`    |
| Write metadata (tags, owners, descriptions) as the end goal | `/datahub-enrich`     |
| Build an ingestion connector for an ML platform             | `/connector-planning` |
| Install the CLI, authenticate, verify connectivity          | `/datahub-setup`      |

**Key boundary:** `/datahub-lineage` traverses the dataset graph and answers "what feeds this table?". This skill answers questions whose subject is a **model, model version, training run, or feature** — where the traversal has to hop between ML entities and datasets, and where the answer depends on run metrics, hyperparameters, and column statistics rather than edges alone. If the user names a model and asks a lineage question, you are in the right skill.

---

## Step 0: Confirm ML Metadata Exists

One search establishes whether the catalog has anything to investigate:

```bash
datahub -C skill=datahub-ml-lineage search "*" \
  --where "entity_type IN (mlModelGroup, mlModel, mlFeatureTable, mlFeature)" \
  --facets-only --format json
```

Interpret the facet counts before going further:

| Observation                                 | What it means                                                                               |
| ------------------------------------------- | ------------------------------------------------------------------------------------------- |
| No ML entities at all                       | No ML source is ingested. Say so and stop — suggest `/connector-planning` for the platform. |
| Models but no `mlFeature`                   | Normal. Only feature stores (Feast, SageMaker Feature Store) emit features.                 |
| Models but no ML training runs (see Step 3) | The model registry was ingested without runs. Provenance questions cannot be answered.      |

Never present "no edges found" as "no dependency exists". Missing ML lineage is far more often missing ingestion. State which of the two you observed.

---

## Step 1: Resolve the Subject Precisely

Users say "the model" for three different entities. Disambiguate before traversing — the wrong one silently produces the wrong answer.

| User means                 | Entity type         | Role                                                        |
| -------------------------- | ------------------- | ----------------------------------------------------------- |
| "the fraud model"          | `mlModelGroup`      | The registered model — a container for all versions         |
| "v7" / "the model in prod" | `mlModel`           | One specific version, with its own metrics and training run |
| "the prediction service"   | `mlModelDeployment` | A running deployment (see the caveat in Step 2)             |

Resolve by name, then confirm:

```bash
datahub -C skill=datahub-ml-lineage search "fraud" \
  --where "entity_type IN (mlModelGroup, mlModel)" \
  --projection "urn type
    ... on MLModelGroup { name properties { description } platform { name } }
    ... on MLModel { name properties { version externalUrl } platform { name } }" \
  --format json --limit 10
```

**If the user names a group but asks a version-specific question** ("why is accuracy down?"), list the versions and ask which one — or default to the latest and say that you did:

```bash
datahub -C skill=datahub-ml-lineage graphql --query '
query {
  mlModelGroup(urn: "<GROUP_URN>") {
    name
    relationships(input: { types: ["MemberOf"], direction: INCOMING, count: 50 }) {
      total
      relationships {
        entity {
          urn
          ... on MLModel {
            name
            properties { version created { time } }
            versionProperties { isLatest version { versionTag } }
          }
        }
      }
    }
  }
}' --format json

# Alternative when the source populated versionSet
datahub -C skill=datahub-ml-lineage graphql --query '
query {
  mlModel(urn: "<MLMODEL_URN>") {
    versionProperties {
      isLatest
      version { versionTag }
      versionSet { urn latestVersion { urn } }
    }
  }
}' --format json
```

**Input validation:** reject shell metacharacters (`` ` ``, `$`, `|`, `;`, `&`, `>`, `<`, `\n`) in names and URNs before passing them to the CLI.

---

## Step 2: Choose the Investigation Mode

| Mode                   | Direction  | Question                                               | Go to          |
| ---------------------- | ---------- | ------------------------------------------------------ | -------------- |
| **Regression triage**  | Upstream   | "Why did this version get worse?"                      | Step 3 → 4 → 5 |
| **Version comparison** | Upstream   | "What differs between v6 and v7?"                      | Step 4         |
| **Provenance audit**   | Upstream   | "What data and code produced this model?"              | Step 3         |
| **Feature root cause** | Upstream   | "Which feature degraded, and where did it come from?"  | Step 5         |
| **ML impact analysis** | Downstream | "Which models break if I change this table or column?" | Step 6         |

Regression triage is the default when the user reports a problem without saying what to look at. Run version comparison **first** — it is one query, and it distinguishes "the recipe changed" from "the data changed" before you spend hops on the dataset graph.

### Choosing your tool: MCP vs. CLI

|                         | MCP tools                                                         | DataHub CLI                                                            |
| ----------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **When available**      | Preferred for search, entity fetch, and lineage traversal         | Required for `--projection`, `graphql`, `timeline`, `lineage --column` |
| **Search**              | `search(query=..., filter=...)`                                   | `datahub search "..." --where "..."`                                   |
| **Batch entity fetch**  | `get_entities(urns=[...])`                                        | `datahub search "*" --where 'urn IN (...)' --projection "..."`         |
| **Lineage**             | `get_lineage(urn=..., upstream=...)`                              | `datahub lineage --urn "..." --direction upstream`                     |
| **Column lineage**      | `get_lineage` / `get_lineage_paths_between` at column granularity | `datahub lineage --urn "..." --column "..." --direction upstream`      |
| **Aspect-level detail** | Not exposed                                                       | `datahub get --urn "..." --aspect <name>`, `datahub graphql`           |

MCP tool names may be prefixed (`mcp__datahub__search`) — match on the function suffix. MCP tools are self-documenting; read their schemas rather than assuming parameters. Several fields this skill needs (`mlTrainingRunProperties`, `datasetProfiles`) are only reachable through `datahub graphql` or `datahub get`, so expect to mix both paths.

**Caveat — `mlModelDeployment` is not in the GraphQL schema.** The entity exists in the metamodel and `mlModelProperties.deployments` holds its URNs, but there is no GraphQL type for it and no `deployments` field on the GraphQL `MLModelProperties`. Read it from the raw aspect instead, and do not try to project it:

```bash
datahub -C skill=datahub-ml-lineage get --urn "<MLMODEL_URN>" --aspect mlModelProperties
```

---

## Step 3: Walk Model → Training Run → Inputs

### Get the model version and its training jobs

`trainingJobs` is **not** a top-level field on the GraphQL `mlModelProperties`. It lives under `mlModelLineageInfo`, which is added to `MLModelProperties` and `MLModelGroupProperties` by a schema extension. Selecting `properties { trainingJobs }` fails with `FieldUndefined`:

```bash
datahub -C skill=datahub-ml-lineage graphql --query '
query {
  mlModel(urn: "<MLMODEL_URN>") {
    urn
    name
    description
    properties {
      version
      type
      externalUrl
      created { time actor }
      hyperParams { name value }
      trainingMetrics { name value }
      mlFeatures
      groups { urn name }
      mlModelLineageInfo { trainingJobs downstreamJobs }
    }
    versionProperties { isLatest version { versionTag } }
    tags { tags { tag { urn } } }
  }
}' --format json
```

Two things to note in the response:

- `mlFeatures` is a list of **URN strings**, not entity objects. Batch-resolve them in one call (Step 5) rather than looping.
- If `mlModelLineageInfo.trainingJobs` is empty, fall back to the relationship graph — some sources emit only the run's output edge, not the model's `trainingJobs`:

```bash
datahub -C skill=datahub-ml-lineage graphql --query '
query {
  mlModel(urn: "<MLMODEL_URN>") {
    relationships(input: { types: ["TrainedBy", "Produces"], direction: INCOMING, count: 20 }) {
      total
      relationships { type direction entity { urn type } }
    }
  }
}' --format json
```

### Inspect the training run

Training runs are `dataProcessInstance` entities carrying the `mlTrainingRunProperties` aspect, with the subtype `ML Training Run`:

```bash
datahub -C skill=datahub-ml-lineage graphql --query '
query {
  dataProcessInstance(urn: "<RUN_URN>") {
    urn
    properties { name created { time actor } externalUrl customProperties { key value } }
    subTypes { typeNames }
    container { urn properties { name } }
    mlTrainingRunProperties {
      id
      outputUrls
      hyperParams { name value }
      trainingMetrics { name value }
    }
    state(limit: 1) {
      status
      timestampMillis
      durationMillis
      result { resultType nativeResultType }
    }
    relationships(input: { types: ["Consumes"], direction: OUTGOING, count: 50 }) {
      total
      relationships { entity { urn type } }
    }
  }
}' --format json
```

Record `properties.created.time` — every time-windowed query later in the investigation should be anchored to the run, not to now.

To find runs without starting from a model, filter by subtype (`entity_subtype` maps to the indexed `typeNames` field). The `dataProcessInstance` entity is indexed in a separate search group, so always pass the entity type filter explicitly rather than expecting runs in a generic keyword search:

```bash
# Training runs
datahub -C skill=datahub-ml-lineage search "*" \
  --where "entity_type = dataProcessInstance AND entity_subtype = 'ML Training Run'" \
  --format json --limit 20

# Experiments, which are containers holding those runs
datahub -C skill=datahub-ml-lineage search "*" \
  --where "entity_type = container AND entity_subtype = 'ML Experiment'" \
  --format json --limit 20
```

### The run's inputs may be stubs, not the real tables

MLflow (and similar sources) register the run's logged datasets as **platform-local dataset references** — an `mlflow` dataset whose only upstream is the real warehouse table, with edge type `COPY`. A one-hop traversal from the run therefore lands on a stub with no schema statistics. Always continue upstream until you reach a dataset on a storage or warehouse platform:

```bash
datahub -C skill=datahub-ml-lineage lineage --urn "<RUN_INPUT_DATASET_URN>" --direction upstream --hops 2
```

Judge the destination by platform (`snowflake`, `bigquery`, `s3`, `databricks`, …), not by hop count.

---

## Step 4: Compare Versions Before Blaming the Data

Fetch the regressed version and the last known good version in one search, then diff three things: metrics, hyperparameters, and the training run's input set.

```bash
datahub -C skill=datahub-ml-lineage search "*" \
  --where "urn IN ('<MLMODEL_URN_GOOD>', '<MLMODEL_URN_BAD>')" \
  --projection "urn type
    ... on MLModel {
      name
      properties {
        version created { time }
        hyperParams { name value }
        trainingMetrics { name value }
        mlModelLineageInfo { trainingJobs }
      }
    }" \
  --format json
```

Read the diff as follows:

| Observation                                | Interpretation                                                                                  |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| Hyperparameters differ                     | Candidate cause. Stop and report before traversing data lineage.                                |
| Hyperparameters identical, metrics moved   | Points at the data. Continue to Step 5.                                                         |
| Input dataset sets differ between the runs | Training data scope changed — often the whole explanation.                                      |
| Both runs `SUCCESS`                        | Says nothing about data quality. A successful run on degraded input is the normal failure mode. |

**Metrics live in three places; do not conflate them.**

| Location                                  | Meaning                                                          |
| ----------------------------------------- | ---------------------------------------------------------------- |
| `mlTrainingRunProperties.trainingMetrics` | Measured by that specific run — the authoritative offline number |
| `mlModelProperties.trainingMetrics`       | Snapshot copied onto the version at ingestion                    |
| `mlModelProperties.onlineMetrics`         | Production serving metrics                                       |

If offline training metrics are flat but the user reports a production problem, the training data is not implicated — look at serving-time skew, the deployed version, and the feature freshness path instead. Check which version is actually deployed (`versionProperties.isLatest` plus the raw `deployments` aspect from Step 2); serving an older version than the registry's latest is a common and easily missed explanation.

---

## Step 5: Trace Features to Source Columns, Then Profile Them

### Resolve features and their sources

`mlModelProperties.mlFeatures` gives URNs; resolve them in one batch. Each `mlFeature` carries `properties.sources`, the datasets it derives from (`DerivedFrom`). Features roll up into an `mlFeatureTable` via `Contains`, but the **feature** is the unit a model consumes:

```bash
datahub -C skill=datahub-ml-lineage search "*" \
  --where "urn IN ('<MLFEATURE_URN_1>', '<MLFEATURE_URN_2>')" \
  --projection "urn type
    ... on MLFeature {
      name featureNamespace
      properties { description dataType sources { urn properties { name } platform { name } } }
    }" \
  --format json
```

`get_entities(urns=[...])` is the MCP equivalent. For the whole feature table and its keys:

```bash
datahub -C skill=datahub-ml-lineage graphql --query '
query {
  mlFeatureTable(urn: "<MLFEATURETABLE_URN>") {
    name
    properties {
      description
      mlFeatures { urn name properties { dataType sources { urn } } }
      mlPrimaryKeys { urn name }
    }
  }
}' --format json
```

### Do not trust a clean feature table

**This is the most important judgment in the skill.** Feature pipelines routinely `COALESCE` nulls to zero, impute defaults, or filter bad rows. A feature table can profile at zero nulls while its source column has been 60% null for two weeks — the corruption is silently converted into a plausible-looking constant, and the model degrades with no null-rate signal anywhere near the model.

So: never conclude "the features are fine" from a feature-table or feature-store profile. Traverse **column-level** lineage to the source column and profile there.

```bash
# Column-level upstream from the feature's serving table
datahub -C skill=datahub-ml-lineage lineage \
  --urn "<SOURCE_DATASET_URN>" --column "<COLUMN>" --direction upstream --format json
```

MCP alternative: `get_lineage` at column granularity, or `get_lineage_paths_between` to see the intermediate transformations and the SQL that produced them. When the transformation SQL is available, read it — a `COALESCE`, `IFNULL`, `NVL`, or `WHERE x IS NOT NULL` on the path is direct evidence that upstream damage is masked downstream. `get_dataset_queries` on the intermediate table serves the same purpose when no column-level edge exists.

If column-level lineage is missing, say so and fall back to table-level lineage plus column-name matching — but label that inference as inference.

### Profile the source column across the run window

`datasetProfile` is a timeseries aspect. Window it to bracket the training runs you are comparing, so you see the change rather than today's state:

```bash
datahub -C skill=datahub-ml-lineage graphql --query '
query {
  dataset(urn: "<SOURCE_DATASET_URN>") {
    datasetProfiles(startTimeMillis: <GOOD_RUN_TIME_MS>, endTimeMillis: <BAD_RUN_TIME_MS>, limit: 20) {
      timestampMillis
      rowCount
      fieldProfiles { fieldPath nullCount nullProportion uniqueCount min max mean median }
    }
  }
}' --format json
```

Look for, in rough order of diagnostic value: a step change in `nullProportion`; `uniqueCount` collapsing to 1 (a column pinned to a constant); `mean`/`median` shifting outside historical range; `rowCount` dropping. Compare the profile nearest the good run against the one nearest the bad run — a single snapshot proves nothing.

Pair it with the schema and ownership history for the same window:

```bash
datahub -C skill=datahub-ml-lineage timeline --urn "<SOURCE_DATASET_URN>" --category technical_schema --start 30daysago
```

A column rename, type change, or drop that lands between two training runs is a complete explanation on its own. `datahub-quality` can then tell you whether an assertion already caught it.

---

## Step 6: ML Impact Analysis (Downstream)

When the subject is a dataset or column and the question is which ML assets depend on it:

1. **Datasets → features.** Find features whose `sources` include the dataset:

   ```bash
   datahub -C skill=datahub-ml-lineage graphql --query '
   query {
     dataset(urn: "<DATASET_URN>") {
       relationships(input: { types: ["DerivedFrom"], direction: INCOMING, count: 100 }) {
         total
         relationships { entity { urn type ... on MLFeature { name featureNamespace } } }
       }
     }
   }' --format json
   ```

2. **Features → models.** For each feature, find the models that consume it (`Consumes`, incoming).

3. **Datasets → training runs.** Runs that consumed the dataset directly (`Consumes`, incoming on the dataset), then their output models (`Produces`, outgoing on the run). Remember the stub-reference hop from Step 3 — if the platform-local reference is what the run consumed, query relationships on that URN too.

4. **Models → deployments and downstream jobs.** `mlModelProperties.mlModelLineageInfo.downstreamJobs` (`UsedBy`) plus the raw `deployments` list.

5. **Rank by blast radius.** A feature used by one retired model is not the same finding as a feature used by three production deployments. Report models with a deployment, or whose `versionProperties.isLatest` is true, first.

Cap traversal at 100 related entities per hop and confirm with the user before going wider. Present with `templates/ml-impact-analysis.template.md`.

---

## Step 7: Present the Finding

Lead with the conclusion and a confidence level, then the evidence chain, then what you could not check. Use `templates/model-investigation.template.md` for triage and `templates/ml-impact-analysis.template.md` for impact.

Rules for the write-up:

1. **One sentence of conclusion first.** "Accuracy dropped because `customer_age` in the source table went 62% null between the two runs."
2. **Show the chain as a chain**, each hop with the URN or name that produced it:

   ```text
   fraud_detector v7 (mlModel)
     └─ TrainedBy → run-8f21 (ML Training Run, 2026-06-14)
          ├─ metrics: accuracy 0.71 (v6: 0.94)
          └─ Consumes → mlflow ref: customer_features
               └─ upstream → snowflake prod.analytics.customer_features
                    └─ column customer_age ← raw.crm.customers.age
                         └─ nullProportion 0.02 → 0.62 on 2026-06-11
   ```

3. **Separate observation from inference.** Profiles and metrics are observations. "The null spike caused the regression" is an inference — say which it is.
4. **Quantify.** "3 of 11 features" and "0.02 → 0.62", not "some features" and "much worse".
5. **List the gaps.** No column-level lineage, no profiles on the source, no runs ingested — each of these bounds your conclusion and the user needs to know.
6. **Offer the next step**, not a lecture: an assertion on the source column (`/datahub-quality`), a documented finding (`/datahub-enrich` or `save_document`), or ownership notification for the affected models.

### Recording findings

If the user wants the investigation captured in the catalog, that is a write operation: present the exact change, get explicit approval, then execute — or hand off to `/datahub-enrich`. Useful targets are a description or document on the model version, a tag on the source column, and an owner notification. Never write a conclusion into the catalog as a side effect of investigating.

---

## Reference Documents

| Document                     | Path                                            | Purpose                                                           |
| ---------------------------- | ----------------------------------------------- | ----------------------------------------------------------------- |
| ML entity model reference    | `references/ml-entity-model-reference.md`       | ML entity types, URNs, aspects, relationship names, GraphQL paths |
| ML investigation patterns    | `references/ml-investigation-patterns.md`       | Traversal recipes per investigation mode, with stop conditions    |
| Model investigation template | `templates/model-investigation.template.md`     | Regression / provenance findings report                           |
| ML impact analysis template  | `templates/ml-impact-analysis.template.md`      | Downstream ML impact report                                       |
| CLI reference (shared)       | `../shared-references/datahub-cli-reference.md` | CLI syntax, MCP equivalents, GraphQL discovery commands           |

---

## Common Mistakes

- **Selecting `properties { trainingJobs }` on a model.** It is `properties { mlModelLineageInfo { trainingJobs downstreamJobs } }`. The flat field does not exist in GraphQL and returns `FieldUndefined`.
- **Confusing the model group with the model version.** Metrics, hyperparameters, and training runs belong to the version. Answering a version question with group metadata produces a confidently wrong answer.
- **Trusting a clean feature profile.** Zero nulls in a feature table does not mean the source is healthy — transforms mask upstream damage. Trace to the source column and profile there.
- **Stopping at the run's first input.** MLflow-style sources emit platform-local dataset references; the real table is one hop further upstream. Judge by platform, not hop count.
- **Treating a `SUCCESS` run as evidence of good data.** Training almost always succeeds on degraded input. That is why this workflow exists.
- **Profiling "now" instead of the run window.** `datasetProfiles` is a timeseries — window it around the runs being compared, using the run's `created.time`.
- **Reporting "no lineage" when metadata was never ingested.** Distinguish "no edges exist" from "this source does not emit edges". Check Step 0 first.
- **Iterating one URN at a time.** `mlFeatures` and `trainingJobs` are URN lists — batch-resolve with `get_entities` or a `urn IN (...)` search, not N+1 lookups.
- **Guessing GraphQL field names.** Verify with `datahub graphql --describe MLModel --recurse --format json` or `--list-operations` before inventing a field. Use `--strip-unknown-fields` on read queries as a safety net, never on mutations.
- **Expecting `mlModelDeployment` in GraphQL.** No GraphQL type exists. Read `deployments` from the raw `mlModelProperties` aspect.

## Red Flags

- **User input contains shell metacharacters** → reject, do not pass to the CLI.
- **Zero ML entities in the catalog** → stop and report the ingestion gap; do not improvise an answer from dataset lineage alone.
- **Traversal exceeding 100 entities at a hop, or beyond 3 hops** → confirm with the user before expanding.
- **A conclusion resting on one profile snapshot** → get the comparison point or downgrade the confidence.
- **User asks for a write** ("tag the bad column", "document this") → present the plan, get approval, or hand off to `/datahub-enrich`.
- **Question is really about dataset lineage or assertion health** → redirect to `/datahub-lineage` or `/datahub-quality`.

---

## Remember

- **Version, not group.** Resolve which one you are looking at before anything else.
- **Compare two versions before you traverse data.** A hyperparameter diff is one query and it often ends the investigation.
- **Anchor every time window to the training run**, not to the current timestamp.
- **The feature table is not the source of truth.** Follow column-level lineage to the source column, and read the transformation SQL for `COALESCE`-style masking.
- **Offline metrics and production metrics answer different questions.** Match the evidence to the symptom the user reported.
- **Absence of edges is usually absence of ingestion.** Say which one you observed.
- **Show the chain.** A hop-by-hop trace with names and numbers is the deliverable; a verdict without it is not.
