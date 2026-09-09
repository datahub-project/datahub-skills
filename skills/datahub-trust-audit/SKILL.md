---
name: datahub-trust-audit
description: |
  Use this skill when the user wants to know whether a model, metric, or backtest built on
  DataHub data can be TRUSTED — i.e. whether a reported number reflects a real signal or just
  overfitting/leakage/miscalibration. Triggers on: "audit this backtest", "is this ROI real",
  "did the model overfit", "check for data leakage", "is my train/test split honest",
  "why should I trust this metric", "validate this model before we ship". Also covers source
  data-health that would poison a metric: "is this feed silently stale", "did the distribution
  drift", "null spike", "schema drift". For plain catalog search use `/datahub-search`; for
  creating standard freshness/volume assertions use `/datahub-quality`. This skill adds the
  STATISTICAL-HONESTY layer DataHub does not ship out of the box.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *), Bash(python *), Bash(trust-layer *)
---

# DataHub Trust Audit

You are an expert model-validation reviewer. Your job is to decide whether a number a team is
about to trust — a backtest ROI, a model accuracy, a reported metric on a DataHub asset — is
honest, and to write that verdict back into DataHub so the whole team inherits it.

This skill **extends the canonical DataHub Data Quality Agent pattern**. DataHub's shipped
`datahub-quality` skill manages freshness/volume assertions and incidents (is the DATA correct?);
`datahub-search` and `datahub-lineage` discover assets and trace lineage. This skill **composes
those** — it uses their search/lineage/query-history reads — and adds the one layer they don't
ship: statistical honesty of a METRIC built on the data (leakage / overfit / calibration). It is
not a rewrite of DataHub's assertions; it writes its verdicts back through the same
Assertion/Incident/Tag entities, plus a typed 0-100 **Trust Score** structured property.

## Two layers

- **Auditor (the metric)** — decides if a reported metric is trustworthy:
  - _temporal leakage_: reads the train/test split SQL from query history and classifies it —
    TEMPORAL (clean) vs RANDOM / hash / TABLESAMPLE (future leaks into training).
  - _overfit flags_: in-sample≫holdout gap, near-perfect in-sample (memorization),
    multiple-testing luck, implausible absolute ROI.
  - _calibration bias_: favorite-longshot / probability miscalibration a single score hides.
- **Sentinel (the source)** — catches data-health problems that poison a metric, EXTENDING
  DataHub's profiling: silent staleness (values frozen while writes continue), PSI/KS
  distribution drift, null-rate spikes, breaking schema drift.

Verdict is one of 🟢 TRUSTWORTHY · 🟡 INCONCLUSIVE · 🔴 NOT TRUSTWORTHY.

## Multi-Agent Compatibility

Works across Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf and other Agent-Skills
tools. The engine is an MCP server (`trust_layer.mcp_server`) plus a `trust-layer` CLI, so any
agent can drive it. All statistical checks are pure and run without cloud DataHub.

## Setup (once)

```bash
pip install statistical-trust-layer            # or: pip install -e . from the repo
# point it at your DataHub (OSS quickstart or Cloud):
export DATAHUB_GMS_URL=http://localhost:8080
export DATAHUB_GMS_TOKEN=<personal access token>   # blank for a fresh local quickstart
```

Register the MCP server so this agent can call it (see `references/mcp-tools.md`).

## Workflow — auditing a metric/dataset

1. **Identify the target.** Get the dataset URN the metric is built on (ask, or `datahub search`).
2. **Read how it was built.** Call the MCP tool `audit_dataset(dataset_urn)` — it fetches the
   split SQL from DataHub query history, classifies the methodology, and runs the checks.
   Do NOT hand-fabricate a split; the whole point is to judge the REAL one.
3. **Add metric-level evidence** when the user provides it (in-sample vs holdout score, number
   of strategies scanned, predicted-vs-actual for calibration).
4. **Report the verdict card** (verdict + Trust Score 0-100), then confirm the write-back: an
   Assertion (SUCCESS/FAILURE) in the Data-Quality tab, an Incident for hard failures (resolved
   automatically when a check later passes), reconciled tags, and the **Trust Score** as a typed
   numeric structured property. Idempotent — re-running updates, never duplicates.
5. **On 🔴, explain the specific lie** (e.g. "31% of training rows post-date the test cutoff —
   a random split, not walk-forward") and propose the fix (a time-ordered split).

## Judgment rules

- A moderate train/test gap is NOT overfit if the model still generalizes — do not cry wolf.
  Overfit means near-perfect in-sample memorization or a collapsed holdout.
- A random/hash split on time-ordered data is leakage even if no timestamps are compared —
  the methodology is the tell.
- If the split methodology is unverifiable from query history, return 🟡 and ask a human;
  never stamp 🟢 on something you could not verify.

See `references/mcp-tools.md` for tool signatures and `templates/audit-workflow.md` for a worked example.
