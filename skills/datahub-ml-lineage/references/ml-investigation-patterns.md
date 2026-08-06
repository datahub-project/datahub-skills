# ML Investigation Patterns

Traversal recipes for each investigation mode, with the evidence each step produces and the conditions under which to stop.

---

## Pattern 1: Regression Triage

**Goal:** explain why a model version performs worse than its predecessor.

**Strategy:**

1. Resolve the regressed version and the last known good version (both `mlModel`, same group).
2. Diff hyperparameters and metrics between the two versions. If hyperparameters differ, stop — report that and let the user decide whether to keep digging.
3. Resolve each version's training run through `mlModelLineageInfo.trainingJobs`.
4. Diff the runs' input dataset sets. A different input set is often the whole answer.
5. For inputs common to both runs, walk to the real source dataset (past any platform-local stub) and compare `datasetProfiles` at each run's timestamp.
6. Check `timeline --category technical_schema` on those datasets for the window between the two runs.

**Key question:** "What is different between the two runs, in this order: recipe, input set, input contents?"

**Stop when:** you find a difference that is sufficient to explain the metric movement, or you have checked all three layers and found none — in which case report that the metadata does not explain it and name what is missing (usually profiles or column-level lineage).

---

## Pattern 2: Version Comparison

**Goal:** answer "what changed between v6 and v7?" without a performance claim attached.

**Strategy:**

1. Fetch both versions in one search with `urn IN (...)`.
2. Tabulate: version tag, created time, hyperparameters, training metrics, training run URN, feature list.
3. Fetch both runs; tabulate run duration, outcome, experiment container, input datasets.
4. Present as a two-column diff, marking rows that are identical as such rather than omitting them.

**Key question:** "Which fields differ, and which are identical?"

**Stop when:** the diff is complete. Do not extend into data lineage unless the user asks — comparison is a factual deliverable on its own.

---

## Pattern 3: Provenance and Reproducibility Audit

**Goal:** establish what produced a model version, and whether that is enough to reproduce it.

**Strategy:**

1. Model version → training run → run's inputs, hyperparameters, `outputUrls`, and experiment container.
2. Run → `InstanceOf` parent template (the `dataJob` or `dataFlow`), if the source emits one — that is the pipeline definition.
3. For each input dataset, resolve to the real source and record its platform, environment, and last schema change.
4. Check the model-card aspects (`mlModelTrainingData`, `intendedUse`, `mlModelMetrics`) for documented context.
5. Score the gaps explicitly.

**Reproducibility checklist:**

| Element                         | Where it comes from                                     | Missing means                                  |
| ------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| Hyperparameters                 | `mlTrainingRunProperties.hyperParams`                   | Cannot reconstruct the configuration           |
| Training data identity          | Run's `Consumes` edges                                  | Cannot identify what it learned from           |
| Training data state at run time | `datasetProfiles` near the run timestamp                | Cannot tell whether the data has since changed |
| Code or pipeline reference      | `InstanceOf` parent, `externalUrl`, `sourceCode` aspect | Cannot re-execute                              |
| Artifact location               | `mlTrainingRunProperties.outputUrls`                    | Cannot retrieve the produced model             |
| Owner                           | `ownership` on the model or group                       | No one to ask                                  |

**Key question:** "Could someone else rebuild this version from what DataHub knows?"

**Stop when:** every checklist row is either resolved or recorded as a gap.

---

## Pattern 4: Feature Degradation Root Cause

**Goal:** find where a feature's values went wrong.

**Strategy:**

1. Model → `mlFeatures` → batch-resolve the features.
2. Feature → `properties.sources` → the datasets it derives from.
3. For the suspect feature, traverse **column-level** lineage upstream from its source column.
4. At each hop, read the transformation SQL where available (`get_lineage_paths_between`, or `get_dataset_queries` on the intermediate table).
5. Profile the **source** column across the relevant window, not the feature table.
6. Confirm against schema history on the source.

**The masking pattern — the reason this order matters:**

A feature pipeline that applies `COALESCE(age, 0)`, `IFNULL`, `NVL`, a default-value fill, or `WHERE col IS NOT NULL` converts upstream nulls into plausible values or silently drops rows. Downstream of that transform, `nullProportion` stays at zero while the underlying column degrades. Signals that survive the mask, in order of usefulness:

| Signal at the source                     | What it usually indicates                          |
| ---------------------------------------- | -------------------------------------------------- |
| `nullProportion` step change             | Upstream extraction or join broke                  |
| `uniqueCount` collapsing toward 1        | Column pinned to a constant or a default fill      |
| `mean` / `median` shifting outside range | Unit change, scale change, or partial backfill     |
| `rowCount` drop with stable nulls        | Rows filtered out rather than nulled               |
| Schema change in the window              | Rename or type change silently changed the mapping |

Post-mask, look instead at the feature's distribution moments (`mean`, `median`, `stdev`) and at `distinctValueFrequencies` — a spike in one categorical value is the fingerprint of a default fill.

**Key question:** "Where in the chain did the value stop being real?"

**Stop when:** you reach a dataset with no upstream lineage, or you find the hop where the statistics change. If lineage runs out before the statistics change, say so — the cause is outside the catalog.

---

## Pattern 5: ML Impact Analysis

**Goal:** enumerate the ML assets a dataset or column change would affect.

**Strategy:**

1. Dataset → features (`DerivedFrom`, incoming).
2. Features → models (`Consumes`, incoming).
3. Dataset → training runs (`Consumes`, incoming) → models (`Produces`, outgoing). Also check any platform-local reference dataset that points at this dataset, since runs consume the reference rather than the table.
4. Models → deployments (raw `deployments` aspect) and downstream jobs (`UsedBy`).
5. Group results by model group, then rank.

**Ranking rule:** blast radius, not edge count.

| Priority | Criterion                                                    |
| -------- | ------------------------------------------------------------ |
| 1        | Model has a deployment                                       |
| 2        | Model version is `isLatest` in its group                     |
| 3        | Feature is used by more than one model group                 |
| 4        | Model's only source for that feature is the changing dataset |
| 5        | Model version is superseded and has no deployment            |

For a column-level change, filter step 1 by the affected column using column-level lineage rather than reporting every feature on the table — a table-level answer over-reports and gets ignored.

**Key question:** "Which models are serving traffic that depends on this?"

**Stop when:** all model groups reachable in two ML hops are enumerated, or the result exceeds 100 entities — then summarize by group and ask before expanding.

---

## Pattern 6: Training / Serving Divergence

**Goal:** test whether the data a model was trained on is the data it is now served.

**Strategy:**

1. Training side: run → input datasets → real source datasets.
2. Serving side: model → features → `properties.sources`.
3. Compare the two dataset sets. Divergence is not automatically a bug — offline training frequently reads a warehouse table while serving reads an online store fed from it — so check whether the two are connected by lineage.
4. If they are connected, compare profiles on both sides in the same window.
5. If they are not connected by any lineage path, that is a finding: the serving path is unverifiable from the catalog.

**Key question:** "Is the serving source the same data, a copy of it, or something else entirely?"

**Stop when:** the relationship between the two sets is established as same / derived / unrelated.

---

## Cross-Cutting Rules

### Time alignment

Anchor every window to metadata timestamps, never to now:

| Anchor                                        | Use for                                |
| --------------------------------------------- | -------------------------------------- |
| `dataProcessInstance.properties.created.time` | Profile windows, timeline start        |
| `mlModel.properties.created.time`             | When the version was registered        |
| `datasetProfile.timestampMillis`              | Which profile corresponds to which run |
| `timeline --start`                            | Schema and ownership change windows    |

A profile taken today tells you about today. The investigation is about the interval between two runs.

### Hypothesis discipline

Enumerate candidate causes, then look for the evidence that would rule each one out. Report the survivors, not the first plausible story.

| Hypothesis                 | Confirms it                                             | Rules it out                                   |
| -------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| Configuration change       | Hyperparameter diff between versions                    | Identical hyperparameters                      |
| Training data scope change | Different input dataset sets between runs               | Identical input sets                           |
| Upstream data corruption   | Source column statistics shift in the run window        | Stable statistics across the window            |
| Schema change              | Timeline event on a source dataset in the window        | No schema events in the window                 |
| Deployment mismatch        | Deployed version is not the version whose metrics moved | Deployed version matches the regressed version |
| Serving-time issue only    | Offline metrics flat while production metrics moved     | Offline metrics moved too                      |

### Confidence

| Level      | Warranted when                                                                      |
| ---------- | ----------------------------------------------------------------------------------- |
| **High**   | A metadata observation is time-aligned to the change and alternatives are ruled out |
| **Medium** | The observation is time-aligned but alternatives are unchecked or unverifiable      |
| **Low**    | The correlation exists but the mechanism is inferred, or key metadata is missing    |

State the level and the reason for it. Never present a Low-confidence chain in the register of a conclusion.

### Traversal limits

- Cap ML-graph traversal at 3 hops and 100 entities per hop without confirmation.
- Batch-resolve URN lists; never issue N+1 lookups over `mlFeatures` or `trainingJobs`.
- Prefer one search with `urn IN (...)` and a projection over repeated `get` calls.
