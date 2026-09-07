# datahub-evals

Run DataHub's saved evals, and report answers — yours or another agent's — for DataHub's own
judge to score.

## How it works

There is no script. The skill drives it:

1. `acryl-datahub-cloud evals list|get` fetches the evals and their conditions.
2. You show the plan and get a yes — one eval is one full agent run.
3. Each eval is answered in a **fresh agent** with the DataHub tools attached: a subagent, or
   `claude -p` when the tool surface needs constraining.
4. `acryl-datahub-cloud evals report` sends the answer **without a verdict**, so DataHub scores it with
   the same judge it uses for its own runs.
5. `acryl-datahub-cloud evals history` reads the verdict back.

Every call to DataHub is one CLI subcommand, so the queries and the payload live in the CLI
rather than being reimplemented here.

## Requirements

- **`acryl-datahub-cloud` with its evals extra** — the DataHub Cloud CLI, which pins its own
  `acryl-datahub`, so give it its own environment:

  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install 'acryl-datahub-cloud[datahub-evals]'
  ```

  Quote the extra — an unquoted `[...]` is a glob in `zsh`. The extra carries `graphql-core`,
  without which the CLI's schema-compatibility checks silently do nothing.

  A `datahub evals` form is coming, but no shipped release wires the group into the `datahub`
  CLI, so the skill uses `acryl-datahub-cloud evals` throughout.

- **A DataHub connection** — `~/.datahubenv`, or `DATAHUB_GMS_URL` + `DATAHUB_GMS_TOKEN`.
- **[datahub-sql-workflow](https://github.com/datahub-project/datahub-skills/tree/main/skills/datahub-sql-workflow)**,
  loaded where a fresh agent sees it (user level or the plugin, not project level) — `SQL`
  evals are scored on catalog-grounded SQL, and that skill is what grounds it.
- **A DataHub MCP server** the answering agent can reach, pointing at the same instance the
  results go to. `claude mcp list` shows what is configured; servers are scoped per project
  directory, so where you run from decides what exists.

## The two things it exists to prevent

**A verdict nobody produced.** Asked to score an answer "the way DataHub would", an agent can
produce something that reads authoritative and is comparable with nothing. `--type` is never
passed, so the answer goes to DataHub's own judge.

**A failure that is really a formatting artifact.** `ASSET_REFERENCE` is scored against
`citedEntities`, which DataHub extracts from markdown links whose target is a URN — a bare
URN in prose extracts nothing. `acryl-datahub-cloud evals report --dry-run` will not catch this: it
validates the request, never the eval's conditions. So the skill has the agent check each
`mustReference` URN against the answer before reporting, and confirm against `citedEntities`
afterwards.

The answer is reported **verbatim**. Rewriting prose into links to make a condition pass
would score a text nobody produced.

## No code

There is nothing to run here but the CLI and an agent, so there is nothing to test. The skill
is `SKILL.md`.
