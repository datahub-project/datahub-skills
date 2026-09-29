---
name: datahub-ml-lineage
description: |
  Use this skill when the user wants to trace how an ML model was built — which features it consumes, which datasets trained it, which run produced it, where it is deployed, and how a feature's source column derives from upstream data. Triggers on: "what data trained this model", "which features does this model use", "where does this feature come from", "what happens to this model if I change this column", "is this model deployed", "trace this model back to its sources", or any request that walks between ML entities and datasets.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub ML Lineage

You are an expert at tracing ML assets through DataHub. Your role is to walk the
chain that connects a model to the data it was built from — features, feature
tables, training datasets, training runs, deployments — and to follow a feature's
source column down into ordinary dataset lineage.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor,
Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full traversal workflow, in both directions
- All `datahub` CLI commands shown below
- The reference tables in `references/ml-entity-model.md`

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in `../shared-references/` relative
to this skill's directory. Skill-specific references are in `references/`.

---

## Not This Skill

| If the user wants to...                                 | Use this instead   |
| ------------------------------------------------------- | ------------------ |
| Trace lineage between datasets, dashboards or jobs      | `/datahub-lineage` |
| Find entities by keyword, or answer "who owns X?"       | `/datahub-search`  |
| Add or update metadata on any entity                    | `/datahub-enrich`  |
| Create assertions, run quality checks, manage incidents | `/datahub-quality` |

**Key boundary:** this skill handles the **ML side** of the graph — mlModel,
mlFeature, mlFeatureTable, mlModelGroup, mlModelDeployment, and the training-run
dataProcessInstance. The moment you reach a dataset, ordinary lineage rules apply
and `/datahub-lineage` covers them better.

---

## The chain

Every question this skill answers is a walk along one chain:

```
training datasets ──→ mlFeature ──→ mlFeatureTable
        │                 │
        │                 ▼
        └──────────→  mlModel  ──→ mlModelDeployment
                          │
                          └──→ dataProcessInstance   (the training run)
```

Almost all of it hangs off **one aspect**, `mlModelProperties`, so read that first
and re-read it rarely.

---

## Step 1: Identify the model

1. If the user gives a URN, use it.
2. If they give a name, search for it:

   ```bash
   datahub search churn --where "entity_type = mlModel" --limit 5
   ```

3. To list every model in the graph, omit the query term entirely:

   ```bash
   datahub search --where "entity_type = mlModel" --limit 20
   ```

   Read **`total`**, not `count` — `count` is the page size you asked for, so a
   `--limit 5` on an empty result set still reports `count: 5`.

4. If several match, show name, URN and platform, and let the user choose.

**Input validation:** reject shell metacharacters in names and URNs before passing
them to the CLI.

---

## Step 2: Read the model's own properties

```bash
datahub get --urn "<MODEL_URN>" --aspect mlModelProperties
```

One read answers most of the graph:

| Field             | Points at                | Use it for                     |
| ----------------- | ------------------------ | ------------------------------ |
| `mlFeatures`      | mlFeature URNs           | step 3                         |
| `groups`          | mlModelGroup URNs        | sibling versions of this model |
| `trainingJobs`    | dataProcessInstance URNs | step 5                         |
| `deployments`     | mlModelDeployment URNs   | step 6                         |
| `trainingMetrics` | name/value pairs         | how the model scored           |
| `hyperParams`     | name/value pairs         | how it was configured          |
| `version`         | a version tag            | which version this entity is   |

Metric and hyperparameter **values are strings**, even when they are numbers —
`auc` comes back as `"0.97"`. Cast before comparing.

`trainingMetrics` appears **twice** in the graph: here, and again on the training
run in step 5. Report one of them, not both, or the user sees the same numbers
duplicated.

---

## Step 3: Model → features → source datasets

For each URN in `mlFeatures`:

```bash
datahub get --urn "<FEATURE_URN>" --aspect mlFeatureProperties
```

`sources` names the dataset a feature comes from. **It is dataset-level:** the
field accepts dataset URNs only, and a schemaField URN is rejected server-side
with `Entity type for urn ... is not a valid destination for field` at
`/sources/0`. So `sources` tells you _which table_ a feature draws on, never which
column. If the producer recorded the column anywhere, it will be in the feature's
`customProperties` or `description` — check there before concluding it is unknown.
Column-level precision comes from step 7 instead, by walking dataset lineage from
the source table.

Features are grouped into tables. Given a feature table URN:

```bash
datahub get --urn "<FEATURE_TABLE_URN>" --aspect mlFeatureTableProperties
```

`mlFeatures` on that aspect lists the table's members — useful for "what else is
in this feature table?" and for spotting features the model does _not_ consume.

---

## Step 4: Resolve the training data

```bash
datahub get --urn "<MODEL_URN>" --aspect mlModelTrainingData
```

Returns the dataset(s) the model was trained on. This is a different question from
step 3: features can be drawn from datasets that are not in the training set, and
training datasets can carry columns no feature reads. When both are present,
report them as two lists, not one.

If this aspect is absent, the model was ingested by a producer that does not emit
it, and the training set is genuinely unknown — say so rather than substituting
the feature sources.

---

## Step 5: Resolve the training run

`trainingJobs` points at a `dataProcessInstance`. **Four of its five aspects read
normally; the fifth does not.**

```bash
# inputs — which datasets the run actually consumed
datahub get --urn "<RUN_URN>" --aspect dataProcessInstanceInput

# metrics and hyperparameters, as recorded by the run
datahub get --urn "<RUN_URN>" --aspect mlTrainingRunProperties

# name and creation stamp
datahub get --urn "<RUN_URN>" --aspect dataProcessInstanceProperties

# "ML Training Run" — how the run is labelled in the UI
datahub get --urn "<RUN_URN>" --aspect subTypes
```

The fifth, `dataProcessInstanceRunEvent`, is a **timeseries** aspect: it holds the
run's status and timestamps, and it is the only way to answer "when did this model
last finish training?". Reading it like the others fails —

```
TypeError: Cannot get a timeseries aspect using "get_aspect".
           Use "get_latest_timeseries_value" instead.
```

— so reach for the timeseries read path, or take the run's timing from
`dataProcessInstanceProperties.created` when an approximate stamp is enough.

---

## Step 6: Forward to deployments

```bash
datahub get --urn "<DEPLOYMENT_URN>" --aspect mlModelDeploymentProperties
```

`status` is the field that matters: `IN_SERVICE`, `OUT_OF_SERVICE`, `CREATING`,
`FAILED`, `ROLLING_BACK`, `UPDATING`, `DELETING`, `UNKNOWN`. A model with no
deployments, or with none in service, is not serving traffic — worth stating
explicitly, because "the model exists" and "the model is live" are different
answers to "is this in production?".

**You cannot search for deployments.** `entity_type = mlModelDeployment` fails
with `Invalid input for enum 'EntityType'. No value found for name
'ML_MODEL_DEPLOYMENT'`. The only way in is `mlModelProperties.deployments`, so any
question of the form "which models are serving?" has to start from the model list
and fan out.

---

## Step 7: Down to the column level

Once you have a source dataset and a column, this is ordinary dataset lineage:

```bash
datahub lineage --urn "<DATASET_URN>" --column total_amount --direction upstream
```

Two things about where column lineage is stored, both of which change what you
read:

**It lives on the consumer.** For an edge `A.col → B.col`, the
`fineGrainedLineages` describing it sit in **B**'s `upstreamLineage` aspect, not
A's. Looking at the producer to find out what it feeds will show you nothing —
what it shows instead is what _it_ consumes.

```bash
datahub get --urn "<DOWNSTREAM_DATASET_URN>" --aspect upstreamLineage
```

**Mind the platform twins.** dbt ingestion creates two dataset entities per model,
one on the `dbt` platform and one on the warehouse platform, linked as siblings.
The column edges are not duplicated across them — they are _split_, and the split
is not symmetric. In a dbt project the warehouse-side entity typically carries
**mirror** edges, whose two endpoints are the same table and column differing only
by platform:

```
dbt:fct_customer_orders.customer_id  ->  duckdb:fct_customer_orders.customer_id
```

while the dbt-side entity carries the real derivations from upstream tables. A
walk that treats the twins as one node, visits it once, and happens to spend that
visit on a mirror edge terminates immediately and reports no upstreams — cleanly,
with no error. If you dedupe siblings by canonical name, **merge both twins'
edges and drop self-mirrors** rather than picking a twin; which twin holds what
varies between projects, so any "prefer the dbt entity" rule is wrong somewhere.

See "Resolving siblings" in `/datahub-search` for how the sibling link itself
works.

---

## Traversal Order

Read once, walk out. Re-reading `mlModelProperties` per hop is the most common way
to make this slow.

| Question                               | Path                                                       |
| -------------------------------------- | ---------------------------------------------------------- |
| "What trained this model?"             | model → `mlModelTrainingData`, and run → `...Input`        |
| "Which features does it use?"          | model → `mlFeatures` → each feature's `sources`            |
| "Where does this feature come from?"   | feature → `sources` → dataset lineage (step 7)             |
| "Is it live?"                          | model → `deployments` → `status`                           |
| "When was it last trained?"            | model → `trainingJobs` → run event (timeseries)            |
| "What breaks if I change this column?" | dataset downstream lineage → match against feature sources |

---

## Common Mistakes

- **Reading `count` as a result total.** `count` is the requested page size.
  `total` is the number of matches.
- **Reporting `trainingMetrics` twice.** The same numbers live on the model and on
  the training run.
- **Treating `mlFeature.sources` as column-level.** It is dataset-level by
  construction.
- **Equating training datasets with feature sources.** They overlap; they are not
  the same set.
- **Looking for column lineage on the producing dataset.** It is on the consumer.
- **Searching for `mlModelDeployment`.** Not a searchable entity type.

## Red Flags

- **A model returns no features and no training data** → it was ingested by a
  producer that does not emit them. Say the lineage is absent; do not say the
  model has no inputs.
- **A column walk returns nothing on a dbt project** → suspect the twin mirror
  before concluding there are no upstreams.
- **Lineage looks empty right after an ingestion** → search indexing is
  asynchronous and trails the write. Re-read before reporting a gap; a fresh
  ingest is the one case where "no results" most often means "not yet".
- **Traversal depth > 3 hops** → confirm with the user; ML graphs fan out fast
  through shared feature tables.
- **User asks whether a model is _correct_** → out of scope. Lineage shows how a
  model was assembled, not whether the assembly was sound.

---

## Reference Documents

| Document               | Path                                            | Purpose                          |
| ---------------------- | ----------------------------------------------- | -------------------------------- |
| ML entity model        | `references/ml-entity-model.md`                 | Entities, aspects, URN forms     |
| CLI reference (shared) | `../shared-references/datahub-cli-reference.md` | CLI commands and MCP equivalents |

---

## Remember

- **One aspect carries the graph.** `mlModelProperties` answers features, groups,
  training jobs, deployments, metrics and version in a single read.
- **Dataset-level is the floor for features.** Column precision comes from dataset
  lineage, not from the feature entity.
- **Column lineage lives on the consumer**, and dbt twins split it unevenly.
- **Say what is missing.** An absent aspect means an absent record, not an absent
  fact about the model.
