---
name: datahub-ml-impact
description: |
  Use this skill when someone wants to know which ML systems break if they change or
  drop a column — downstream impact analysis from a data/schema change to the ML
  features, models, and deployments that depend on it, with the critical distinction of
  whether a model was TRAINED on the column versus only reads it at inference. Triggers
  on: "what ML breaks if I change X", "what models depend on column X", "blast radius of
  dropping X", "is anything trained on X", "will this schema change break a model",
  "downstream ML impact of X", "what happens if I drop this column".
user-invocable: true
allowed-tools: Bash(python *), Bash(pip *)
---

# DataHub ML Impact

Answer, interactively, **"what ML systems break if I change this column?"** This skill
traces DataHub's column-level lineage from a changed column down to the ML features,
models, and deployments that depend on it, and — the part generic lineage can't tell
you — flags whether each model was **trained** on the column (drop it and the model is
quietly wrong) or merely **reads it at inference**.

It is powered by the open-source [Blastradar](https://github.com/datahub-project/datahub)
library: this skill does not reimplement traversal or scoring, it drives Blastradar's
deterministic core (`scripts/ml_impact.py`) and interprets the result.

## When to use this skill

Use it for **impact / "what breaks" questions about ML** stemming from a schema change:
dropping, renaming, or retyping a column and wanting to know the ML blast radius before
merging.

Boundary:

- **`datahub-lineage`** traces generic upstream/downstream edges between any entities.
- **This skill** goes the last mile *into ML*: it scores each impacted model by severity
  and resolves training-run provenance to separate trained-on from inference-only. If the
  question is "what ML models/features/deployments are affected and how badly," use this.

## Prerequisites

1. **Blastradar installed** (it carries the DataHub SDK dependency):
   ```bash
   pip install "blastradar @ git+https://github.com/Pratham-90/blastradar"
   # or, from a Blastradar checkout:  pip install -e .
   ```
2. **A DataHub connection**, via environment variables:
   ```bash
   export DATAHUB_GMS_URL=http://localhost:8080     # your GMS
   export DATAHUB_GMS_TOKEN=...                      # only if metadata auth is on
   ```
   To try it with **no DataHub at all**, point it at Blastradar's recorded fixtures:
   ```bash
   export BLASTRADAR_REPLAY=/path/to/blastradar/tests/fixtures/recorded/datahub_calls.json
   ```
   (Fixtures cover the demo columns: `customers.customer_since`,
   `order_details.order_total`, `customers.phone_number`.)

## Workflow

1. **Identify the column.** Get the `table` (model name) and `column` from the user. If
   they give a DataHub dataset URN or a fuzzy name, help them settle on the model name and
   column; Blastradar resolves the name to a dataset URN and returns `AMBIGUOUS` (all
   candidates) rather than guessing if it's unsure.

2. **Run the impact query** (reuses Blastradar's core — do not reimplement it):
   ```bash
   python scripts/ml_impact.py --table <TABLE> --column <COLUMN>
   ```
   Flags: `--json` for structured output you can parse; `--no-llm` for the deterministic
   templated narration (no API key needed); `--kind RENAME_COLUMN|TYPE_CHANGE` for
   non-drop changes; `--max-hops N` to bound traversal.

3. **Interpret the result** using [`references/ml-impact-reference.md`](references/ml-impact-reference.md):
   read each finding's severity, whether it's `trained on the changed column` vs `reads it
   at inference only`, whether it's deployed, and the lineage path. Note the
   `Why this severity` clause — it traces the score to a rule, deterministically.

4. **Present the answer** with [`templates/ml-impact-report.template.md`](templates/ml-impact-report.template.md).
   Lead with the scariest finding (a **deployed, trained-on** model is the emergency).
   Always surface the trained-vs-inference distinction explicitly — it's the whole point.

5. **Offer next steps:** the suggested migration (deprecate-then-drop), recording the
   finding back into DataHub as an incident + tag + document (needs
   `TOOLS_IS_MUTATION_ENABLED=true`), or running Blastradar's full CI agent on the actual
   PR diff (`blastradar analyze --changes ...`).

## Interpreting severity

Deterministic, first-match-wins (full table in the reference file):

| Severity | Meaning |
|---|---|
| 🔴 critical | Model has an active deployment **and** was trained on the changed column |
| 🟠 high | Model has an active deployment (reads the column at inference only) |
| 🟡 medium | Model depends on the column but has no active deployment |
| ⚪ low | No ML downstream |

Then one-level escalation if the model carries a `Tier1`/`Critical` tag or has an owner.
A result that is **empty but resolved** is a genuine all-clear; a result marked
**incomplete** (unresolved column / truncated walk) is *not* — never report it as safe.

## Reference files

| File | Purpose |
|---|---|
| [`references/ml-impact-reference.md`](references/ml-impact-reference.md) | How the walk works, the severity rules, what "trained-on" means, and the DataHub APIs used |
| [`templates/ml-impact-report.template.md`](templates/ml-impact-report.template.md) | The structure to present the answer in |
| [`scripts/ml_impact.py`](scripts/ml_impact.py) | The runner that drives Blastradar's core for a single column |
