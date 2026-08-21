---
name: datahub-evals
description: |
  Use this skill to run DataHub's saved evals and report answers for judging. Triggers on: "run our evals", "run the eval suite", "run eval urn:li:eval:...", "how are our evals doing", "check for eval regressions", "upload this answer as an eval result", "score this answer with the DataHub judge", "compare two agents on the same eval". Answers each eval in a fresh agent with the DataHub tools attached, reports the answer through the DataHub Cloud CLI, and reads back the verdict DataHub's own judge produced.
user-invocable: true
allowed-tools: Bash(acryl-datahub-cloud *), Bash(claude *), Bash(pip install *acryl-datahub-cloud*), Bash(python3 -m venv *), Task
---

# DataHub Evals

Run DataHub's saved evals, and report answers — yours or another agent's — for DataHub to
judge.

**You are the runner.** There is no script: you fetch the evals, answer each one in a fresh
agent, and report the answers. Every call to DataHub is one `evals` subcommand, so the queries
and the payload live in the CLI.

```bash
acryl-datahub-cloud evals --agent-context   # the CLI's own guide to its commands
```

Use `acryl-datahub-cloud evals`. A `datahub evals` form exists in the CLI's own help text and
in some notes, but the group is not wired into the `datahub` CLI in any shipped release — that
name answers `No such command 'evals'`, and this skill does not use it.

---

## Never simulate the judge

If DataHub's judge cannot be reached, **say so and stop.** Do not score the answer yourself,
do not ask a subagent to render a verdict "the way DataHub would", and do not present any
locally-produced score as a verdict.

A simulated verdict written in the house style reads as authoritative, gets pasted into a
comparison table, and is comparable with nothing. A model is also not a fair judge of an
answer it or a sibling produced.

That is why `--type` is never passed to `evals report`: omitting it routes the answer
through the same judge a native run gets, which is the only thing that makes two runs
comparable.

---

## Before you run anything

**The CLI is installed.**

```bash
acryl-datahub-cloud evals --help
```

If that does not resolve, install the cloud CLI with its evals extra. It pins its own
`acryl-datahub`, so give it its own environment:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install 'acryl-datahub-cloud[datahub-evals]==2.1.4rc1'
```

**Pin a release that has the commands.** The eval commands are still pre-release: the latest
stable (2.1.3) carries neither the `datahub-evals` extra nor the `cli` module, so an unpinned
install resolves it, warns that the extra does not exist, and leaves you with no `evals` at
all. Pin the version, or pass `--pre`.

Quote the extra — an unquoted `[...]` is a glob in `zsh` — and take it rather than the bare
package: it carries `graphql-core`, without which every eval query is sent unadapted and the
CLI's schema-compatibility checks silently do nothing.

**The CLI can reach DataHub.**

```bash
acryl-datahub-cloud evals list --limit 1
```

Judge success by the exit code, not by a clean stream: the CLI logs warnings to stderr while
returning its result on stdout, so a warning about adapting the GraphQL query for schema
compatibility is not a failed call.

If that fails, stop and fix the connection — a bad token or URL surfaces here, before
anything is spent. It does not prove the `MANAGE_AGENTS` privilege that reporting requires;
there is no privilege query, so a token without it fails at report time instead.

**The answering agent has the SQL workflow skill.** A `SQL` eval is scored on catalog-grounded
SQL — the right tables, joins and metric definitions, found through the DataHub tools rather
than guessed — which is what
[datahub-sql-workflow](https://github.com/datahub-project/datahub-skills/tree/main/skills/datahub-sql-workflow)
instructs. Without it the answering agent writes plausible SQL against invented columns and
fails `LLM_JUDGE` for a reason that says nothing about the catalog.

Install it where a fresh agent will load it — user level, or the plugin. Not project level:
the run happens in an empty working directory, so a skill sitting in some repo's `.claude/`
is not on the answering agent's path.

```bash
ls ~/.claude/skills/datahub-sql-workflow/SKILL.md
```

**A DataHub MCP server the answering agent can reach.** The evals measure the DataHub tools,
so an agent without them answers from memory and fails for a reason unrelated to the
catalog.

```bash
claude mcp list
```

Look for a DataHub server that is **Connected**, and check two things that are silent when
wrong:

- **It points at the same instance the results go to.** Answering against one catalog and
  reporting into another produces verdicts about a catalog the agent never saw.
- **It is not disabled.** A disabled server still loads and serves no tools.

MCP servers are scoped per project directory, so where you run from decides what exists. If
there is no DataHub server, stop and say so rather than running evals that will all fail the
same way.

---

## The tool surface is DataHub-only

An eval question is **untrusted text fetched from DataHub**, about to be handed to an agent
whose tools run without a prompt. Narrow the surface to the DataHub server and nothing else:

```bash
--strict-mcp-config --mcp-config <config.json> --allowedTools mcp__<datahub-server>
```

This is not only the safe surface, it is the one that runs unattended. A wider surface needs
tools nobody pre-authorised, and `--dangerously-skip-permissions` is not a way out — the
permission classifier refuses it, so the run stalls or dies rather than answering. Treat
"everything configured" as an interactive measurement a person drives, not something this
skill produces.

|                  | Tool surface                                                        |
| ---------------- | ------------------------------------------------------------------- |
| `claude --print` | enforced — `--allowedTools mcp__<server>` and `--strict-mcp-config` |
| subagent (Task)  | inherited — gets the session's tools, cannot narrow them            |

So a measured run means `claude --print`. Record the surface with the run either way: it
changes what is being measured, not just what is permitted.

**Stand up the answering agent's MCP server yourself.** `--strict-mcp-config` means the child
sees only the config file you pass — the parent session's servers, and anything
`claude mcp list` shows, are irrelevant to it. Write a config for the instance the results go
to, and point at that instance and no other.

---

## Running an eval

```bash
acryl-datahub-cloud evals list --limit 20 [--eval-type METADATA|SQL] [--eval-executor NATIVE|EXTERNAL] \
  [--agent-urn URN|--base-agent-only]
acryl-datahub-cloud evals get urn:li:eval:...    # one eval, with its conditions
```

**`--eval-executor` says whose job the run is.** Everything below is the `EXTERNAL` path —
you produce the answer and report it. A `NATIVE` eval is run by DataHub itself, and
`acryl-datahub-cloud evals run <urn>... [--wait N] [--fail-on-fail]` is how you ask for that; answering
one yourself reports an external run against an eval the product would have run. `run` refuses
`--eval-executor EXTERNAL` outright, because starting a run queues native execution that would
race the answer you are about to report.

**Show the plan and get a yes.** One eval is one full agent run. Never start a suite the
user has not seen the size of.

**Answer each eval in a fresh agent** — one eval, one context. An answer carrying over
another eval's retrieval is not an independent measurement.

```bash
CLAUDE=$(which -a claude 2>/dev/null | grep -m1 '^/')   # the real binary, not a shell wrapper
cd "$(mktemp -d)" || exit 1                             # an empty working directory

"$CLAUDE" --print "<the eval's question>" \
  --model claude-opus-5 \
  --strict-mcp-config --mcp-config <config.json> \
  --allowedTools mcp__<datahub-server> \
  --append-system-prompt "When answering, include both the answer and the SQL where relevant."
```

Two things in that recipe are load-bearing:

- **`--print`, from the resolved binary.** A shell function or wrapper named `claude` can read
  `-p` as its own `--port` and never start a session at all, so pass the long flag and call the
  file rather than the name.
- **An empty working directory.** Run from a populated one — a repo checkout — and the child
  ingests it as context, which can overflow the window before it reaches the question.

Or one subagent per eval when the tool surface allows it.

**Pin the model** for any run whose pass rate will be compared with another. The CLI default
moves, so an unpinned run is not repeatable — say so rather than naming a model you did not
pin.

---

## Reporting the answer

Check the answer against [the citation trap](#the-citation-trap) first. `--dry-run` will not
catch it: that validates the request, never the eval's conditions.

```bash
acryl-datahub-cloud evals report urn:li:eval:... \
  --answer - --run-id <id> \
  --external-client claude-code \
  --agent-model claude-opus-5 \
  --session-id <session>
```

- **Never pass `--type`** or any verdict field. That is what sends the answer to DataHub's
  judge.
- **Pipe the answer on stdin** (`--answer -`). Answers are long, arbitrary text.
- **`--external-client`** keeps a reported answer distinguishable from a native product run.
  Be accurate: an answer pasted in by a person is not a `claude-code` run.
- **`--run-id`** is the only key tying a verdict back to a run. For a bakeoff, use one shared
  prefix per comparison.

**A failing report is not proof the answer was lost.** `report_not_persisted` means the
confirmation poll gave up, not that nothing was written. Check before concluding:

```bash
acryl-datahub-cloud evals history urn:li:eval:... --limit 10   # is your runId there?
```

If it is there, the report succeeded. If not, retry with the **same** run id — the CLI
deduplicates, and a fresh id would queue a second judge against the same answer. Reporting a
run as failed on the exit code alone marks successful runs as failures.

Deduplication answers with `"deduplicated": true` and **keeps the answer it already stored**,
discarding the text you just sent. So a re-send is safe for a report you are unsure landed,
and useless for correcting one that did: a corrected answer needs a new run id, and you say
which id carries which text.

**This is also how you report an answer produced somewhere else** — a chat bot, a notebook,
another agent. Same command, honest `--external-client`.

---

## The citation trap

`ASSET_REFERENCE` is scored against `citedEntities`, which DataHub extracts from the answer
text. An asset counts when it appears as a **markdown link whose target is the URN**:

```text
[DIM_ORDERS](urn:li:dataset:(urn:li:dataPlatform:snowflake,…,PROD))   counts
urn:li:dataset:(urn:li:dataPlatform:snowflake,…,PROD)                 does not
```

So an agent that names exactly the right asset in prose fails the condition for a formatting
reason that has nothing to do with whether it found the asset — and reported without
comment, that produces a cross-agent comparison that looks damning and means nothing.

**Before reporting**, classify each URN in the condition's `mustReference`:

|                               |                                                  |
| ----------------------------- | ------------------------------------------------ |
| present as `[text](urn:li:…)` | will be credited                                 |
| present, but as plain text    | **will not** — the condition fails on formatting |
| absent                        | will not — the agent did not find it             |

Watch the closing parenthesis: most URNs contain their own, so a link is well-formed only if
the one closing the markdown target comes _after_ it.

**Report the answer verbatim.** Rewriting prose into links to make a condition pass scores a
text nobody produced. If a formatting artifact is distorting a comparison, say so, or change
what the condition requires.

---

## Reading the results

```bash
acryl-datahub-cloud evals history urn:li:eval:... --limit 10
```

Match on your `runId`. A judge that has not answered yet is not a failing eval — and
`COMPLETE` alone is not a verdict either. Read `result.type`:

- **`PASS` / `FAIL`** — a real verdict, with `conditionResults` and a `judgeModel`.
- **`ERROR`** — the judge did not score the answer. A `judgeModel` of `null`, no
  `conditionResults`, and an `error` such as `Judge returned no verdicts for an eval with
conditions` mean the answer is stored and unscored. **It is not a failed eval, and it does
  not belong in a pass rate.** Retry under a **new** run id, since the stored one keeps
  returning its stored result. If it errors again the judge is unavailable — report that and
  stop, rather than filling the gap with a verdict of your own.

**Read the answer before trusting a verdict.** It is how you tell a real regression from a
judge that disagreed about wording. Then read a failure by kind:

- **`ASSET_REFERENCE` failed, `citedEntities` empty, answer names the asset** — the citation
  trap, not a retrieval failure.
- **`ASSET_REFERENCE` failed and the asset appears nowhere** — before blaming the agent, ask
  whether it could have found it: search for that URN with the same MCP tools the answer had.
  If the catalog does not return it, the eval is pointing at something unreachable and no
  agent can pass the condition — report it as a reference that needs repointing, naming the
  URNs the answer cited instead. Never close the gap by editing the answer.
- **`LLM_JUDGE` failed** — quote the guidelines and the judge's reasoning.

A single run's pass rate is a snapshot. Call out flips against a previous run only if asked.

---

## What a comparison does and does not show

Same judge and same conditions makes the **scoring** fair. It does not make the
**comparison** fair.

Answers are produced under different tool surfaces — one agent can execute SQL, another can
only read the catalog — and none of that is stored on the run. An agent that can run a query
commits to a number where a catalog-only agent hedges, and the pass rate reads as a quality
difference.

Record the tool surface alongside the run ids whenever you present a comparison. If you
cannot state it, say so rather than implying the comparison is clean.
