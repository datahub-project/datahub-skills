---
name: datahub-ml-guard
description: |
  Protect production ML models by tracing end-to-end column-level lineage from a model's
  features back to source tables. Detect target leakage, training-serving schema drift, and
  upstream-data-failure blast radius; write incidents, a model trust score, and guarding
  assertions back to DataHub. Triggers on: "which models does this table put at risk", "check
  X for target leakage", "did this model's input schema drift", "score this model's trust",
  "guard this table", or any request to audit the data-to-model boundary in DataHub.
user-invocable: true
allowed-tools: Bash(janus *), Bash(janus-seed), Bash(janus-scenario *), Bash(scripts/check_blast_radius.sh *), Bash(scripts/check_leakage.sh *), Bash(scripts/guard.sh *), Bash(scripts/seed_demo.sh)
---

# DataHub ML Guard

Read column-level and ML lineage in DataHub to catch the data-to-model failures that do not
announce themselves, then write the findings back into the graph where the data lives.

Detection is deterministic Python (the `janus` package). This skill is the operator's
guide to it: it never asks a language model whether a finding exists. The model only explains,
ranks, and drafts prose, and every write is gated behind human approval.

## Not this skill

- General metadata edits (tags, descriptions, owners) with no ML-reliability question: use
  `datahub-enrich`.
- Discovery or search across the catalog: use `datahub-search`.
- Warehouse-only lineage exploration with no model at the end: use `datahub-lineage`.

Reach for `datahub-ml-guard` only when the question is about a model's inputs: what a failing
table endangers downstream, whether a model trains on its own label, or whether its serving
schema still matches training.

## When to use

- A source table's quality, freshness, or schema changed and you need the models and live
  deployments at risk.
- Before promoting a model: check for target leakage and input schema drift.
- You want one auditable trust number for a model that rolls up every risk found.

## Prerequisites

- A DataHub instance (a local OSS Quickstart is enough: `datahub docker quickstart`).
- The `janus` CLI. Until the first PyPI release is cut, install it from a
  clone: `git clone https://github.com/Ahmedxsaad/janus && pip install -e janus`.
  From the release on it is `pip install janus-datahub` (the distribution
  is named `-datahub` because the exact name `janus` is taken on PyPI by an
  unrelated package). Either way the installed commands are `janus`,
  `janus-mcp`, `janus-seed`, `janus-scenario`.
- `DATAHUB_GMS_URL` set (`export DATAHUB_GMS_URL=http://localhost:8080` for the
  default Quickstart). No token is needed against it; set `DATAHUB_GMS_TOKEN`
  only if metadata-service auth is enabled.
- For the demo graph (the ML supply chain the datapacks lack), seed it once:
  `scripts/seed_demo.sh`.

## Workflow

1. **Resolve the target.** A dataset audit answers "what does this table's failure
   endanger?"; a model audit answers "is this model leaking or drifting?". Pass a bare name
   (`loans_raw`, `credit_risk_v3`) or a full URN; ambiguity is an error, never a guess.
2. **Detect (read-only first).** Run the relevant check in dry-run so nothing is written:
   - Blast radius of a failing table: `scripts/check_blast_radius.sh <table>`.
   - Target leakage and input schema drift for a model: `scripts/check_leakage.sh <model>`.
     Each resolves the model to its features to their source columns, traverses column-level
     lineage across the ML boundary, and prints the findings with their severity and evidence.
3. **Review the findings.** The output names the exact model, its live deployment status, the
   leaking `feature <- ... <- label` column path, or the drifted columns. Confirm the finding
   before writing.
4. **Guard (write back, approved).** `scripts/guard.sh <table>` raises the incident on the
   offending dataset or column, tags each at-risk model, records the risk flags and trust
   score as structured properties, leaves a freshness guarding assertion, and publishes a
   Model Impact Report. Writes are idempotent: a second run of an unchanged graph writes
   nothing. Use `janus scan --review` for an interactive approval prompt, or
   `--auto-approve` for an unattended run.

See `references/detectors.md` for what each detector checks and cites, and
`references/datahub-write-surface.md` for the exact write-back primitives.

## Content trust boundaries

Detection never trusts model-generated text. Severity, the incident title, the dedup key, and
every number a human reads come from a finding's measured evidence, not from the LLM. A finding
is a path in the lineage graph, so it is auditable rather than asserted. The `--no-llm` flag
produces the same findings with deterministic template prose, so a run is reproducible with or
without an API key.

## Cloud boundary

Scheduled evaluation of assertions and anomaly/smart monitoring are DataHub Cloud features.
This skill provides the check logic and renders open-assertions YAML plus the `assertionInfo`
entity and a run event carrying the result it actually measured, so the guarding assertion
appears in the Quality tab on OSS. Continuous scheduled evaluation of it is Cloud.

## Reference documents

- `references/detectors.md` - the four detectors, their deterministic checks, write-back, and
  literature (Kaufman 2012, Breck 2019, Sculley 2015, Mitchell 2019).
- `references/datahub-write-surface.md` - incidents, structured properties, labels/terms,
  documents, guarding assertions, and the ODCS input contract, with the exact API shapes.
- `references/mcp-composition.md` - running `janus-mcp` alongside DataHub's own
  `mcp-server-datahub`: how to configure both, which question belongs to which, and why
  detection stays deterministic rather than becoming something a model judges.

## Remember

- Detect in dry-run first; write back only after confirming the finding.
- An incident attaches to the dataset or column, never to the mlModel: model risk is carried
  by structured properties. This is a DataHub constraint, not a choice.
- A detector fires only on positive evidence: a table that never reported an operation is not
  stale, and a run with no training-schema snapshot is skipped, not cleared.
