# datahub-evals

Run DataHub's saved evals, and have DataHub's own judge score answers — yours or another
agent's. Real eval runs are recorded and show in the DataHub UI. Ad hoc scores are not.

## How it works

There is no script. The skill drives it:

1. `acryl-datahub-cloud evals list|get` fetches the evals and their conditions.
2. You show the plan and get a yes — one eval is one full agent run.
3. Each eval is answered in a **fresh agent** with the DataHub tools attached: a subagent, or
   `claude -p` when the tool surface needs constraining.
4. The answer goes to DataHub's judge **without a verdict**, so it is scored with the same judge
   DataHub uses for its own runs. Which command sends it decides whether a run is recorded:
   - `acryl-datahub-cloud evals report` records a run of an `EXTERNAL` eval. It shows in the
     eval's run history and pass rate, and `acryl-datahub-cloud evals history` reads the verdict
     back.
   - `acryl-datahub-cloud evals judge` only scores the answer and prints the verdict. Nothing is
     recorded. The skill uses it for "score this answer", comparisons, candidate answers, and any
     answer to a `NATIVE` eval, so those never distort the pass rate.

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

  `evals judge` needs a release that ships it and a DataHub Cloud v2.3.0 or later server.
  Without it the skill asks before recording an answer instead.

- **A DataHub connection** — `~/.datahubenv`, or `DATAHUB_GMS_URL` + `DATAHUB_GMS_TOKEN`.
- **[datahub-sql-workflow](https://github.com/datahub-project/datahub-skills/tree/main/skills/datahub-sql-workflow)**,
  loaded where a fresh agent sees it (user level or the plugin, not project level) — `SQL`
  evals are scored on catalog-grounded SQL, and that skill is what grounds it.
- **A DataHub MCP server** the answering agent can reach, pointing at the same instance the
  results go to. `claude mcp list` shows what is configured; servers are scoped per project
  directory, so where you run from decides what exists.

## The three things it exists to prevent

**A run nobody meant to record.** A recorded run becomes the eval's latest result and moves the
pass rate everyone sees, and the CLI cannot remove it. Only real eval runs are recorded; every
other score goes through `evals judge`.

**A verdict nobody produced.** Asked to score an answer "the way DataHub would", an agent can
produce something that reads authoritative and is comparable with nothing. `--type` is never
passed to `report`, so the answer goes to DataHub's own judge.

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
