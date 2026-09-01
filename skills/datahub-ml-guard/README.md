# DataHub ML Guard

Trace a production ML model's features back through column-level lineage to the
source columns they are computed from, and catch the data-to-model failures that
do not announce themselves: target leakage, training-serving schema drift, and
the blast radius of an upstream table that stopped refreshing.

DataHub holds two graphs no other catalog holds together: column-level lineage
across the warehouse, and ML metadata for the models. Out of the box nothing
joins them, so a model is not connected to a single column and a data failure
cannot be traced to the model it breaks. This skill operates the join and then
reads across it.

## What it does

| Ask                                         | What the skill runs               | What it answers                                                                                            |
| ------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| "Which models does this table put at risk?" | `janus scan --table <t>`          | Every model downstream of a stale table, and which of them are live                                        |
| "Check this model for target leakage"       | `janus scan --model <m>`          | Which feature leaks, and the exact column chain that proves it                                             |
| "Did this model's input schema drift?"      | `janus scan --model <m>`          | Columns added, dropped or retyped since the model was trained                                              |
| "Guard this table"                          | `janus scan --table <t> --review` | Writes an incident, a freshness assertion and an impact report back to DataHub, after you approve each one |
| "What can you even check here?"             | `janus inventory`                 | Per model: what is checkable and what metadata is missing                                                  |

## Why the detection is not a prompt

Detection is deterministic Python in the `janus` package. This skill is the
operator's guide to it: it never asks a language model whether a finding exists.
A leakage verdict is a graph traversal with the column chain as its evidence, so
it is the same answer twice and it survives someone asking "how do you know".
The model explains, ranks and drafts prose; it decides nothing.

That matters most for the failure that is invisible: a missed leak looks exactly
like a clean model. Deterministic detection is what makes a benchmark possible,
and the benchmark is the only reason to believe a recall number.

## Prerequisites

- A DataHub instance (OSS Quickstart is enough; nothing here needs Cloud)
- `DATAHUB_GMS_URL`, and `DATAHUB_GMS_TOKEN` if the instance has metadata
  service authentication enabled
- The `janus` CLI on PATH

No LLM key is required, and no particular vendor: without one, deterministic
template prose is written instead and detection is byte-identical either way.

## Writes it can make

Every write is idempotent and keyed, so rerunning never duplicates:

- an **incident** on the dataset or column at fault
- a **`model-at-risk` tag** and **trust score** on the model
- a **guarding freshness assertion** with its measured result
- a **Model Impact Report** document linked to the model

`--review` pauses before each write and asks. Nothing is written on a plain
read-only question.

## Files

| Path                                  | What it is                                                                    |
| ------------------------------------- | ----------------------------------------------------------------------------- |
| `SKILL.md`                            | The skill itself                                                              |
| `references/detectors.md`             | What each detector needs and what it reports when it lacks it                 |
| `references/datahub-write-surface.md` | Every aspect the write-back touches                                           |
| `references/mcp-composition.md`       | Running alongside `mcp-server-datahub`, and why detection stays deterministic |
| `scripts/`                            | Thin wrappers over the CLI for the common questions                           |
