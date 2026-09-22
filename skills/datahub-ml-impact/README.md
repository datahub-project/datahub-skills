# datahub-ml-impact

A DataHub Skill that answers, interactively: **"what ML systems break if I change this
column?"**

Ask about a column, and the skill traces DataHub's column-level lineage down to the ML
features, models, and deployments that depend on it, scores each by severity, and — the
part a generic lineage view can't give you — tells you whether each model was **trained**
on the column or merely **reads it at inference**.

```
$ python scripts/ml_impact.py --table customers --column customer_since

### ⚠️ ML blast radius: 2 critical, 1 high, 2 medium
🔴 critical — churn_model_v3   trained on the changed column · deployed (IN_SERVICE)
🔴 critical — reactivation_model_v1   reads it at inference only · deployed
🟠 high — churn_model_v1 …   🟡 medium — churn_model_v2, ltv_model_v1
```

## How it's built

It **reuses** the open-source [Blastradar](https://github.com/datahub-project/datahub)
library rather than reimplementing lineage/scoring. `scripts/ml_impact.py` is a thin
driver that calls Blastradar's deterministic core (walk → score → narrate → render) for a
single column. The traversal and severity decisions are plain, reproducible Python; an
LLM is used only to write the explanatory prose (and is optional — `--no-llm`).

## Contents

| Path | What |
|---|---|
| `SKILL.md` | The skill definition (frontmatter + workflow the agent follows) |
| `references/ml-impact-reference.md` | How the walk works, severity rules, trained-on logic, DataHub APIs |
| `templates/ml-impact-report.template.md` | The structure to present an answer in |
| `scripts/ml_impact.py` | The runner that drives Blastradar's core |

## Setup

```bash
pip install "blastradar @ git+https://github.com/Pratham-90/blastradar"
export DATAHUB_GMS_URL=http://localhost:8080     # + DATAHUB_GMS_TOKEN if auth is on
```

Try it with no DataHub by pointing at Blastradar's recorded fixtures:

```bash
export BLASTRADAR_REPLAY=/path/to/blastradar/tests/fixtures/recorded/datahub_calls.json
python scripts/ml_impact.py --table customers --column customer_since --no-llm
```

## License

Apache 2.0, matching both Blastradar and the datahub-skills repository.
