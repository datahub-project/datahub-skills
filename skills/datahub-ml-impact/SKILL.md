---
name: datahub-ml-impact
description: |
  Use this skill when a change to a table or column needs to be judged against the ML models downstream of it, or when a deployed model has changed behaviour and the cause has to be found in the warehouse. Triggers on: "what models does this column reach", "is this feature in a deployed model", "did a protected attribute get into the model", "why did this model change", "impact of this dbt change on ML", "which models consume X", "is this safe to change", or any question that joins a data change to a model in production.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub ML Impact

You are tracing the path between a change in a warehouse and a model that is
serving decisions off it.

This is a different question from ordinary lineage, and answering it with an
ordinary lineage walk produces confident wrong answers. Four things make it
different, and each one has a specific way of failing quietly.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents.

**What works everywhere:** the whole workflow. It uses only the DataHub CLI and
the MCP server, both of which every agent can reach.

**Agent-specific:** `allowed-tools` in the YAML frontmatter above is read by some
agents and safely ignored by others.

**Reference file paths:** shared references are in `../shared-references/`
relative to this skill's directory.

---

## CLI Attribution

When running `datahub` CLI commands, pass `-C skill=datahub-ml-impact` on the
root command so usage can be attributed:

```bash
datahub -C skill=datahub-ml-impact lineage --urn "..." --direction downstream
```

If `-C` is not recognized, omit it. The command works the same without it.

---

## Not This Skill

| If the user wants to...                | Use this instead   |
| -------------------------------------- | ------------------ |
| Trace lineage between tables generally | `/datahub-lineage` |
| Find an entity or ask who owns it      | `/datahub-search`  |
| Set tags, owners or descriptions       | `/datahub-enrich`  |
| Manage assertions and incidents        | `/datahub-quality` |

**Key boundary:** this skill only earns its place when a model is on one end of
the question. If nothing downstream is a model, `/datahub-lineage` is the better
answer and is simpler.

---

## Step 1: Find the entity, and pick the right sibling

A table modelled by dbt and stored in a warehouse exists more than once in
DataHub. dbt, the warehouse platform and any ML platform each hold their own
entity for it, joined as siblings.

```bash
datahub search --query "workforce_features" --entity-type dataset
```

They are not interchangeable, and which one you start from changes the answer:

- **the dbt sibling holds the governance tags.** Tags declared in dbt
  `schema.yml` land here. The warehouse sibling usually has none.
- **the warehouse sibling is what lineage traversal returns.** Start a walk from
  the dbt entity and you can get a shorter path.

**The trap:** ask the warehouse entity whether a column is tagged as a protected
attribute and the answer is no, because the tags are on the sibling. Nothing
errors. A check written this way reports all clear forever. Always resolve
siblings before reading tags, and read the union of what every sibling holds.

---

## Step 2: Walk the column, not the table

A table level walk tells you the feature table is downstream. That is rarely the
question. The question is whether one specific column reaches a model.

```bash
datahub lineage --urn "<dataset-urn>" --direction downstream --column "<column>"
```

Or through the MCP server, `get_lineage` with `column` set.

**The trap:** do not filter the results by column name afterwards. A warehouse
renames as it cleans, so a column can be `public_coverage_flag` in the marts and
`pubcov` in the raw extract. The graph already scoped the walk to that column's
lineage, so every node it returns is on the path by construction. Filtering by
name drops the origin and leaves a shorter answer that reads as complete.

When the name at the far end differs from the name at the near end, say so. The
rename is usually the reason nobody found the column by searching for it.

---

## Step 3: Cross the boundary into the model

Column level lineage stops at the feature table, and that is a fact about the
connectors rather than a gap in the graph. dbt emits column level edges. ML
platforms emit an edge from the training frame to the model with no column on
it, because a training run consumes a table, not a column.

So the walk runs in two stages:

1. follow the column downstream while column edges exist
2. from every table it lands in, walk downstream again without a column filter
   to reach models, training runs and deployments

**The trap:** stopping after stage one reports that the column reaches no model.
That is the most expensive wrong answer available here, because it is the exact
question that was asked and the answer sounds like good news. Count hops from
the start of stage one so the distance does not reset.

---

## Step 4: Separate deployed from merely registered

A model existing in the catalog says nothing about whether it is serving. Most
registries hold far more archived and experimental versions than live ones, and
a change that reaches forty registered models and no live one is a different
change from one that reaches a single live model.

Read the stage from the registry rather than inferring it:

- MLflow writes the registry stage as a tag on the model, so
  `mlflow_production` and `mlflow_staging` mean somebody promoted it, and
  `mlflow_archived` means the opposite.
- The environment in a model urn, usually `PROD`, is the fabric the entity lives
  in. It is not a statement that anything is serving. Treating it as one reports
  every registered experiment as deployed.

Rank the answer by consequence: deployed models first, however many hops away,
then everything else.

---

## Step 5: Say what the change means, not only what it touches

If the column carries a governance tag, that belongs at the top of the answer
rather than under a dependency tree. The useful shape is:

> `<column>` is `<tag>`. It reaches `<n>` deployed model(s): `<names>`, `<n>`
> hops through `<intermediate tables>`. It enters the warehouse at
> `<source table>.<original name>`, defined in `<file>`.

If more than one column arrived in the same window, name all of them and say
that the graph cannot tell which one is responsible. Do not rank them by
plausibility. An invented single cause is worse than an honest pair.

---

## Working backwards, from a model that moved

Same graph, opposite direction. Start from the model, walk upstream to the
training frame, then walk each feature column upstream to its origin. Compare
the model's current feature set with the one from its previous training run: the
columns it gained are where to look first.

Two things worth stating in the answer:

- **the direction the quality metric moved.** If accuracy went up, every monitor
  that watches model quality had no reason to object, and saying so explains why
  nothing caught it earlier.
- **when the column arrived**, from the run timestamps, so the answer names a
  moment and not only a column.

---

## A note on reading responses over MCP

The MCP server trims responses so an answer fits in a model's context window.
Fields present through an in process SDK call can be absent over MCP, and `type`
on search results is one of them. Derive entity type from the urn rather than
the field. No transport can trim the urn, because it is the identifier.

---

## Checking your own answer

Before returning, confirm each of these. Any no means the answer is not ready.

- Did you read tags from every sibling, not just the entity you walked?
- Did you avoid filtering the walk by column name?
- Did you run stage two to cross into models?
- Did you read the deployment stage from the registry rather than the urn?
- If nothing was found, can you say what you looked at, so "no impact" is a
  result rather than a silence?
