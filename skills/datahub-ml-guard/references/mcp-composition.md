# Running alongside DataHub's own MCP server

Two MCP servers, side by side, answering different kinds of question about the
same graph. This is a worked example, not a dependency: nothing in Janus
imports or requires `mcp-server-datahub`, and both work alone.

## Why two, and why they must stay two

[`acryldata/mcp-server-datahub`](https://github.com/acryldata/mcp-server-datahub)
is the general one. It exposes the catalog to a model as _questions_: search
entities, read lineage, look up a dataset's schema, find who owns something. That
is exactly right for open-ended work, where the model's job is to explore and the
answer is a judgement a human then reads.

`janus-mcp` (`pip install "janus-datahub[mcp]"`) exposes three tools
and nothing else: `check_leakage`, `check_freshness`, `check_gate`. Each one runs
a deterministic detector and returns what it measured. **The model is not asked
whether a finding exists.** It is told, and it explains.

That difference is the whole point of running both, and it is worth being
explicit about, because the tempting design is to skip Janus entirely and
ask a capable model to read the lineage and judge for itself. Do not:

- **The answer must be reproducible.** "Does `credit_risk_v3` leak?" has one
  correct answer for a given graph, and it must be the same answer twice. An
  LLM reading a lineage graph gives a plausible answer, not a stable one, and
  the two are indistinguishable to the person reading it.
- **The evidence must be checkable.** A leakage finding from `check_leakage`
  carries the literal chain of columns the traversal walked. A judgement carries
  a paragraph. Only one of those survives somebody asking "how do you know".
- **Catalog text is attacker-reachable.** Anyone who can edit a dataset
  description can write instructions into it. When detection is deterministic,
  a successful injection changes prose and nothing else, because it is
  downstream of the detectors. When detection _is_ the model, it changes the
  verdict.
- **A wrong "no" is invisible.** A missed leak looks exactly like a clean model.
  Deterministic detection is what makes a benchmark possible, and the benchmark
  is the only reason anyone should believe the recall number.

So: the official server for what a catalog _contains_, Janus for what a
model's data _is doing wrong_. Composing them gives a model both, and neither
one has to grow into the other.

## Configuring both

Both speak stdio, so an MCP client runs them side by side. For Claude Desktop,
in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "datahub": {
      "command": "uvx",
      "args": ["mcp-server-datahub"],
      "env": {
        "DATAHUB_GMS_URL": "http://localhost:8080"
      }
    },
    "janus": {
      "command": "janus-mcp",
      "env": {
        "DATAHUB_GMS_URL": "http://localhost:8080"
      }
    }
  }
}
```

Check the upstream README for that server's own current invocation and
authentication; the block above is the shape, not a pin. Both read
`DATAHUB_GMS_URL`, and both take `DATAHUB_GMS_TOKEN` when the instance has
metadata-service authentication enabled.

## What a combined session looks like

The pattern that makes the pairing worth having: the general server narrows the
question, Janus answers the part that has to be right.

> **"We are about to promote the churn model. Anything I should know?"**
>
> 1. `datahub` search resolves `churn_model` and reads its `mlModelProperties`:
>    one training run, an input dataset, an owner, no deployment yet.
> 2. `datahub` lineage shows the input table's upstreams, which is context a
>    human wants and no Janus tool provides.
> 3. `janus` `check_leakage` answers the question that decides the
>    promotion, with the column chain as evidence.
> 4. `janus` `check_gate` gives the same verdict as a policy: pass, block,
>    or "could not tell", which is what the CI job will return.

And a second one, starting from the table rather than the model:

> **"Which of our models are affected by `loans_raw` being stale?"**
>
> 1. `janus` `check_freshness` measures the staleness and traverses the
>    blast radius into the ML graph, naming the models and which are live.
> 2. `datahub` then answers the follow-ups a person always asks next: who owns
>    each of those models, what else consumes the table, which domain it is in.

## Read-only, on both sides of this

Every Janus MCP tool is annotated `readOnlyHint: true` and calls its scan in
dry-run with no flag to turn that off. The model on the other end of an MCP
client is outside this project's control, so it gets to ask what is wrong and
never to fix it. Writing back is `janus scan` and `janus gate --write`,
run by a human who typed the command, or `janus watch`, which is
unattended by design and says so.

There is one intentional gap on the other server, and Janus's OSS
contribution aims at it: `mcp-server-datahub` has no tool for writing an
incident. [`mcp_ext/raise_incident_tool.py`](https://github.com/Ahmedxsaad/janus/blob/main/mcp_ext/raise_incident_tool.py)
is a thin, parameterised `raise_incident` for it, and
[`mcp_ext/RFC-ml-incidents.md`](https://github.com/Ahmedxsaad/janus/blob/main/mcp_ext/RFC-ml-incidents.md)
argues for first-class ML incidents underneath it.
