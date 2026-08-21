# obsel Collaboration

The order of operations an agent follows when several agents work on the same data and obsel is
watching the swarm.

## What it does

1. Checks every input for staleness before any work starts
2. Registers the task's reads and writes as lineage, once
3. Announces the run, so obsel does not flag work that is in flight
4. Reports the real output files, so obsel fingerprints them itself
5. Reads back which finished work the completion just invalidated, and hands it to the operator

## Capabilities

- **Input check** — five verdicts per table, including the two that are not all-clears
- **Lineage declaration** — short table names only; obsel builds the URNs
- **Volatile columns** — declare the columns that move every run, once, so a re-run marks nothing
- **Completion report** — identical output reports no change, which is what makes the loud answers
  worth believing
- **Failure handoff** — abandon after announcing, so no task is left invisible at `running`

## Usage

```
> check whether clean_orders went stale before I read it
> register my revenue_rollup task with obsel
> report my completion and tell me what it invalidated
```

## Requires

obsel running, with its MCP server connected. See https://github.com/bayshores/obsel.
