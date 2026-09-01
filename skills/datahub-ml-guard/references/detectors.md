# The detectors

Each is deterministic Python: it reads the graph, applies a threshold, and returns typed
findings. None call a language model and none write; the write-back is a separate, idempotent
step. Findings are auditable because the evidence is a fact DataHub already holds (a lineage
path, a schema snapshot, an operation timestamp), not a model's assertion.

Seven finding types ship. The four below are documented in full because they are the ones a
first-time reader needs; the three that follow read the same graph the same way and are
summarised at the end.

| Finding type         | What it says                                                |
| -------------------- | ----------------------------------------------------------- |
| `upstream-freshness` | A table past its SLA, and the models downstream of it       |
| `target-leakage`     | A feature that derives from its own label column            |
| `input-schema-drift` | The training-time schema no longer matches the input's      |
| `sensitive-source`   | A feature derives from a column the organization classified |
| `deprecated-input`   | A model trains on a table its owners marked deprecated      |
| `proxy-candidate`    | A feature shares an ancestor with a protected attribute     |
| `table-level-risk`   | The degraded answer for a model with no column-level link   |

## Target leakage (the flagship)

**Question:** does a model consume a feature derived from its own label?

Target leakage does not announce itself. Nothing breaks, no job fails. The model reports an
accuracy it does not have because one of its features encodes the answer, and it collapses in
production where the label does not exist yet at scoring time. Offline metrics cannot catch it:
a held-out split validates the same contaminated data. Only the lineage can catch it.

The detector resolves each of a model's features to its source column, walks that column's
upstream cone, and reports every column that reaches a declared label. A label is declared by a
glossary term on the column, read from two places and unioned: `glossaryTerms` on the
`schemaField` (what Janus and the seeder write) and `editableSchemaMetadata` on the parent
dataset (what the DataHub UI writes when a human tags a column by hand). So a data scientist
declares their label in the UI, touching no Janus configuration, and detection starts
working.

One trap matters: `get_lineage(source_column=...)` returns the upstream **dataset**, not the
upstream column. The column identity survives only in `LineageResult.paths`
(`LineagePath(urn, entity_name, column_name)`). The detector reads `paths` and never `urn`, and
that same `feature <- ... <- label` path is what the incident quotes.

**Write-back:** a `FIELD` incident on the leaking `schemaField` (never on the model), a
`leakage-risk` glossary term on the feature, and a `risk_flags` structured property on the
model.

Cite: Kaufman et al., "Leakage in Data Mining" (2012).

## Blast radius (upstream failure)

**Question:** which models does a failing table put at risk?

Lineage crosses out of the warehouse and into ML entities: both `MLFeature.sources`
(`DerivedFrom`) and `MLModelProperties.mlFeatures` (`Consumes`) declare `isLineage: true`, so
one downstream call spans the supply chain:

```
loans_raw --(UpstreamLineage)--> customer_features   hop 1, dataset
          --(DerivedFrom)------> mlFeature            hop 2
          --(Consumes)---------> mlModel              hop 3
```

A deployment is not reachable this way (`deployments` declares `DeployedTo` without
`isLineage`), so it is read from the model's own aspect. That distinction decides severity: a
model behind a live endpoint is the only one scoring live traffic on stale data, so live is
CRITICAL, deployed-but-idle is HIGH, undeployed is MEDIUM.

Detection triggers on positive evidence only: a freshness lag beyond the SLA (read from the
dataset's `operation` timeseries aspect), or a planted scenario. A table that never reported an
operation is not stale; a deployment with no properties aspect is not live.

**Write-back:** a `FRESHNESS` (or `VOLUME`) incident on the offending dataset, the
`model-at-risk` tag and risk-flag properties on each model, a freshness guarding assertion with
the measured run event, and a Model Impact Report.

Cite: Sculley et al., "Hidden Technical Debt in Machine Learning Systems" (NeurIPS 2015), which
names the failure: _undeclared consumers_.

## Schema drift (training-serving skew)

**Question:** does a model's input schema still match the one it was trained on?

Training-serving skew hides in a passing pipeline. A column is retyped, dropped, or added
upstream weeks after training, and the serving pipeline feeds the live model values it was
never trained to parse. Nothing errors; the model keeps scoring on inputs that no longer mean
what they meant at training.

The training-time schema is not reconstructed from fragile catalog version history. It is
captured on the training run when the model is trained (a JSON `field_path -> native_type` map
per input dataset, in the run's `customProperties`), and the detector diffs each input's
current `schemaMetadata` against that frozen snapshot: added, removed, and retyped columns.
This is exactly how TFX/TFDV guard against skew. A run with no snapshot is skipped, not
cleared: absence of a baseline is not absence of drift.

**Write-back:** a `DATA_SCHEMA` incident on the drifted input dataset (never on the model),
quoting every changed column, plus the `model-at-risk` tag and the `input-schema-drift` risk
flag on the model.

Cite: Breck et al., "Data Validation for Machine Learning" (MLSys 2019).

## Trust score

**Question:** one auditable number for a model that rolls up every risk found.

A deterministic weighted sum of the findings a scan produced about a model, plus whether anyone
owns it. The weights are configuration:

```
trust = 100
  - 40 * (upstream_assertion_failing)
  - 20 * (has_leakage_finding)
  - 15 * (has_schema_drift)
  - 15 * (freshness_lag_hours / SLA_hours, capped)
  - 10 * (missing_owner)
score in [0,100] -> band: healthy (>=70) / watch (>=40) / at-risk
```

A model is scored only against what the scan actually checked: a scan that audited freshness
and leakage but not drift cannot deduct for drift it never looked for. The LLM never touches
the number.

**Write-back:** `janus.trust_score` (number) and `janus.trust_band` (string) as
structured properties on the mlModel, plus a rollup Model Impact Report.

Cite: Sculley et al. 2015 (surrounding debt dominates reliability) and Mitchell et al.,
"Model Cards for Model Reporting" (FAT* 2019).

## The three governance detectors

These read the part of the graph somebody else already filled in: a classification, a
deprecation flag, a protected-attribute term. Nothing about the data is wrong; what is wrong
is what a model was allowed to see, or that it depends on something with a decommission date.

**Sensitive source** is the leakage walk with a different mark. A feature derives, through
column lineage, from a column tagged or termed as restricted. It reports the same auditable
chain. It is configuration-gated and has no default: with no classification named it reports
**not evaluated**, never clean, because a guessed classification URN either matches nothing or
matches a term that means something else in your catalog.

```bash
JANUS_SENSITIVE_TAG_URNS=urn:li:tag:PII,urn:li:tag:Confidential
JANUS_SENSITIVE_TERM_URNS=urn:li:glossaryTerm:Classification.Restricted
```

**Deprecated input** needs no configuration: `deprecation` is DataHub's own aspect with one
meaning everywhere. A model trains on a table its owners marked deprecated, and neither team
has a way to know about the other. Capped at `medium` severity, because it is a deadline
rather than a defect.

**Proxy candidate** finds a feature that shares an ancestor with a protected attribute without
either descending from the other. It is reported for human review and never as discrimination,
capped at `medium`: two columns sharing an ancestor is a structural fact, and whether that
makes one a stand-in for the other is a question about the data that no walk of a metadata
graph can answer.

## Table-level risk, the degraded mode

Until a model is linked, none of the column-level checks can run on it. Rather than only
listing what it could not do, a scan reports what it _can_ see about the tables the model
trains on: past its freshness SLA, deprecated, or holding a classified column.

It is its own finding type and never merged with the others, because it answers a weaker
question with weaker evidence. It says so out loud, quoting the measured precision of
table-level reasoning (0.25) against the question precision answers: which feature carries the
problem. It never outranks a column-level finding. `janus link` is what upgrades it.
