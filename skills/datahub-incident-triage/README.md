# datahub-incident-triage

On-call triage for data incidents — diagnose a broken asset by walking DataHub lineage, then write the conclusion back into the catalog.

## What it does

- **Parses** a free-text incident report or an alert JSON (dbt, Airflow, Monte Carlo) into a structured incident and resolves the names to concrete DataHub URNs
- **Searches memory first** — past postmortems stored as DataHub documents steer the investigation before it starts, instead of decorating it afterwards
- **Computes the blast radius** downstream with a deterministic impact score, and reports the deduplicated list of owners to notify
- **Ranks root-cause hypotheses** with cited evidence URNs: schema drift upstream, query change, an already-degraded ancestor, a source-side issue, or a historical precedent
- **Proposes the write-back as a dry run** — incident tags, an incident banner on the asset, owners for governance gaps — and applies it **only after explicit approval**
- **Saves the postmortem** back to DataHub, which is what the next investigation retrieves

## Usage

```
> orders in order_entry_db is showing NULL values in customer_id since 03:00 UTC
> the exec revenue dashboard numbers are wrong, figure out what broke
> triage this: {"asset": "analytics.order_history", "check": "freshness", "status": "fail"}
> /datahub-incident-triage order_details is stale since yesterday
```

## Requirements

Read-only triage works against any DataHub deployment. The write-back steps need the MCP mutation tools enabled (`TOOLS_IS_MUTATION_ENABLED=true`, plus `TOOLS_IS_USER_ENABLED=true` for owner assignment), or a `datahub` CLI with permission to run GraphQL mutations.

The memory loop needs the DataHub document tools (`search_documents`, `grep_documents`, `save_document`). If they are absent the skill still works — it treats it as a cold start.

## Reference implementation

[Hindsight](https://github.com/gmassello/hindsight) (Apache-2.0) implements this workflow as a deterministic phase state machine with an LLM inside each phase, plus a web UI and an audit log. Its `examples/` directory holds full captured runs against a live DataHub:

- [`02-cold-vs-warm`](https://github.com/gmassello/hindsight/tree/main/examples/02-cold-vs-warm) — the same incident twice. Memory cut the investigation from 20 DataHub calls to 15, and the warm run swept 6 consumers against the cold run's 29.
- [`04-skill-portability`](https://github.com/gmassello/hindsight/tree/main/examples/04-skill-portability) — an agent following only `SKILL.md`, with none of that implementation in the loop, reaching the same root cause and the same owner list.
