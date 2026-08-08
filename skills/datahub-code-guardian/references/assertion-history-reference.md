# Assertion history reference

How to read what earlier runs concluded about an asset. This is Step 2 of the skill, and it is the read that stops one agent from redoing another agent's work.

**On the acronym:** DataHub uses MCP for both Metadata Change Proposal and, in agent tooling, the Model Context Protocol. Every mention below means the Model Context Protocol server, `mcp-server-datahub`.

## Where each capability lives

| Capability                                                         | Core (OSS) | Cloud |
| ------------------------------------------------------------------ | ---------- | ----- |
| Read schema, ownership, tags, terms, lineage                       | Yes        | Yes   |
| Read assertions and their run history                              | Yes        | Yes   |
| `upsertCustomAssertion` + `reportAssertionResult` (write verdicts) | Yes        | Yes   |
| `addLink` institutional memory receipt                             | Yes        | Yes   |
| Native assertion monitors, incidents, subscriptions                | No         | Yes   |

The whole guardian loop works on Core. If `datahub` is not configured and no DataHub agent tools are present, hand off to `/datahub-setup` before reading anything.

## What you are reading

An external tool records its verdicts as **custom assertions**. Each check and asset pair is one assertion, and each run reports one result against it. So the history of an asset is a set of assertions, each carrying a run timeline, and each run carrying the reason it reached its verdict in `nativeResults`.

| Layer                        | Holds                                                  |
| ---------------------------- | ------------------------------------------------------ |
| `assertion.info.description` | Which check this is, and what it measures              |
| `assertion.info.externalUrl` | Where the full report lives                            |
| `runEvents.runEvents[]`      | One entry per run, oldest and newest both available    |
| `result.type`                | `SUCCESS`, `FAILURE`, or `ERROR` for that run          |
| `result.nativeResults`       | The reason, as flat key and value pairs the tool chose |

## The read, via GraphQL

```graphql
query AssertionHistory($urn: String!, $count: Int!) {
  dataset(urn: $urn) {
    assertions(start: 0, count: $count) {
      total
      assertions {
        urn
        info {
          type
          description
          externalUrl
        }
        runEvents(limit: $count) {
          total
          failed
          succeeded
          runEvents {
            timestampMillis
            status
            result {
              type
              nativeResults {
                key
                value
              }
            }
          }
        }
      }
    }
  }
}
```

`runEvents` is available directly under an assertion, so one query per asset returns every check and its whole timeline. Do not rely on server ordering — sort by `timestampMillis` yourself, because the current state is the newest event and the "since when" is the oldest event of the current unbroken streak.

Read a single assertion the same way when you already have its URN:

```bash
datahub -C skill=datahub-code-guardian graphql --query '
query {
  assertion(urn: "<ASSERTION_URN>") {
    info { type description externalUrl }
    runEvents(limit: 10) {
      total failed succeeded
      runEvents { timestampMillis status result { type nativeResults { key value } } }
    }
  }
}' --format json
```

## Finding the assertions a tool wrote

Assertions are searchable entities, so an estate-wide question does not need a dataset in hand.

```bash
datahub -C skill=datahub-code-guardian search "*" \
  --where "entity_type = assertion" --format json --limit 20
```

Health filters find the assets to look at first:

```bash
datahub -C skill=datahub-code-guardian search "*" \
  --where "entity_type = dataset AND hasFailingAssertions = true" \
  --format json --limit 20
```

## Reading it through the Model Context Protocol server

`mcp-server-datahub` is the preferred read path when it is connected, and its coverage differs by deployment. Observed against DataHub Core 1.6.0 with `mcp-server-datahub` 0.6.0:

| Tool                        | Core (OSS)                         | Cloud             |
| --------------------------- | ---------------------------------- | ----------------- |
| `search`                    | Yes, for datasets and other assets | Yes               |
| `get_entities`              | Yes, for datasets                  | Yes               |
| `list_schema_fields`        | Yes                                | Yes               |
| `get_lineage`               | Yes                                | Yes               |
| `get_lineage_paths_between` | Yes                                | Yes               |
| `get_dataset_queries`       | Yes                                | Yes               |
| `get_dataset_assertions`    | **Not registered**                 | Yes, when enabled |

Three practical notes follow from that.

`get_dataset_assertions` is gated twice. It is registered only when `DATA_QUALITY_TOOLS_ENABLED=true`, and it declares a Cloud minimum version, so the version filter removes it from `tools/list` on a Core server. On Core, take the assertion history through `datahub graphql` with the query above.

`get_entities` on a dataset URN returns `health`, which is the fastest signal that an asset has failing checks at all, but it does not return the assertion list. Use it to triage, then read the timeline with GraphQL.

`search` filtered to `entity_type = assertion` returns the right number of hits with each result stripped down to its bare `urn`, because the tool's projection carries no `Assertion` fragment. Read the assertion timeline through `datahub graphql` on Core, or hydrate each URN through `get_entities`, which does project assertions in full.

## What to extract

Four fields decide what you do next. Everything else is detail for the report.

| What                | Where                                                     |
| ------------------- | --------------------------------------------------------- |
| Current state       | `result.type` of the newest run                           |
| State since when    | `timestampMillis` of the oldest run in the current streak |
| Last failure reason | `nativeResults` of the newest failing run                 |
| Repair outcome      | A `repair` key in `nativeResults`                         |

## Property keys worth recognising

`nativeResults` is free-form, so a reader cannot assume keys. These are the ones the writeback convention in `verdict-writeback-reference.md` recommends, and recognising them makes a history from another tool readable.

| Key           | Meaning                                                   |
| ------------- | --------------------------------------------------------- |
| `rule`        | The check identifier, stable across runs                  |
| `measurement` | The measured value against the allowed one                |
| `findings`    | How many findings this run reported                       |
| `repair`      | `offered`, `previewed`, `applied`, or `refused`           |
| `reasons`     | The first few finding messages, joined                    |
| `reasoning`   | A model's stated reasoning, when the check was a judgment |
| `confidence`  | That model's confidence as a unit fraction                |

A `repair` of `refused` is the single most important value in this table. It means a human or a policy already rejected the fix you are about to propose.
