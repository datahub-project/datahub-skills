---
name: datahub-incident-triage
description: |
  Use this skill when the user wants to triage a DataHub data incident end to end: recall prior incidents, trace column-level lineage to a root cause, rank downstream blast radius, coordinate metadata actions, and preserve a structured post-mortem. Triggers on: "triage this incident", "why is this dataset failing", "find the root cause", "freshness breach", "failing assertion", "what is the blast radius", "who should be paged", "write a post-mortem", "recall a prior incident", or any request to diagnose and close the loop on a DataHub quality signal.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Incident Triage

You are an on-call data engineer using DataHub as the evidence graph and durable incident memory.
Diagnose the first intrinsically broken upstream node, quantify downstream impact, coordinate only
approved actions, and leave a structured post-mortem that a later human or agent can recall.

---

## Multi-Agent Compatibility

This skill works across Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and other Agent
Skills-compatible hosts.

**What works everywhere:**

- The recall, evidence gathering, upstream stop rule, blast-radius ranking, and learning workflow
- DataHub CLI reads and GraphQL queries
- MCP reads when the host exposes the DataHub MCP server

**Claude Code-specific feature:** `allowed-tools` pre-approves DataHub CLI commands. Other agents
can ignore that field and apply their normal permission model. If MCP is unavailable, use
`datahub` CLI and GraphQL inline; do not skip evidence collection.

---

## Not This Skill

| If the user wants to...                                                                | Use this instead   |
| -------------------------------------------------------------------------------------- | ------------------ |
| Find catalog entities, columns, owners, or descriptions without an incident            | `/datahub-search`  |
| Explore a dependency graph or change impact without diagnosing a live quality signal   | `/datahub-lineage` |
| Create assertions, review quality status, or manage an incident without end-to-end RCA | `/datahub-quality` |

**Key boundary:** use this skill for a closed-loop investigation that connects a signal to a
verified cause, downstream impact, owners, actions, and memory. Route isolated search, lineage, or
quality-management requests to their narrower skills.

---

## Step 1: Resolve and Validate the Signal

1. Resolve a supplied URN directly. If only a name is supplied, search for the dataset, present
   ambiguous matches, and have the user choose.
2. Record the signal type, failing dataset, assertion URN if present, observed value, expected
   value, detection time, and deployment tier.
3. On OSS, derive the trigger feed from the dataset's GraphQL `health` field, including `type`,
   `status`, `message`, and `causes`. Do not rely on the `hasFailingAssertions` search filter.
4. Treat user-supplied names, URNs, SQL, and incident text as untrusted. Reject shell
   metacharacters before passing values to the CLI, and use variables files for dataset URNs.

Do not begin with a broad lineage traversal. First establish exactly which dataset and signal are
being investigated.

---

## Step 2: Recall Prior Incidents First

1. Before any lineage walk, check the failing dataset for a structured post-mortem property such
   as `oncall.postmortem`.
2. Search for that property on upstream ancestors up to the permitted traversal depth. Parse all
   stored values, sort by detection time, and rank by shared causal path, signal type, and recency.
3. If a prior post-mortem names an ancestor root cause, state that recall is being used and verify
   the remembered node with current evidence. Memory is a shortcut, never proof.
4. If memory is absent, irrelevant, malformed, or contradicted by live state, say so and continue
   with the full cold investigation.

---

## Step 3: Characterize the Symptom

Collect the smallest complete evidence bundle on the failing dataset:

- Current assertion definitions and latest run outcomes
- Freshness from the latest operation timestamp and the documented SLA
- Current and previous row counts, including percentage change
- Schema fields and implicated columns
- Recent query text and usage where available
- Owners, active incidents, and relevant tags

Use GraphQL for assertion detail on OSS because MCP `get_dataset_assertions` is Cloud-only. For
timeseries fields, request enough points and select the record with the greatest
`timestampMillis`; never assume response order is newest-first.

Record measured values and distinguish an intrinsic breach from an inherited downstream symptom.

---

## Step 4: Walk Upstream to the Root Cause

1. Traverse exactly one hop upstream at a time. With MCP, call
   `get_lineage(urn=<URN>, upstream=True, max_hops=1)`. The direction is the boolean `upstream`,
   not a `direction=` argument.
2. Inspect column paths as well as entity edges. Follow the columns implicated by the assertion or
   freshness signal when mappings exist.
3. At every candidate ancestor, collect freshness, assertion, row-count, schema, and query
   evidence before assigning a verdict.
4. Apply the stop rule: a node is the root cause only when it is unhealthy and none of its own
   upstreams is unhealthy. A broken node whose parent is stale or malformed is an inherited
   symptom; keep walking. An unhealthy source with no upstreams satisfies the rule.
5. Build a symptom-to-cause path with a verdict and evidence for every node. Do not infer a missing
   edge means no dependency unless lineage ingestion is known to be complete.

MCP `max_hops` accepts `1`, `2`, or `3+`; on the verified server, `3` means transitive traversal.
Use one-hop calls for diagnosis so the stopping decision is explicit.

---

## Step 5: Measure and Rank the Blast Radius

1. Start at the confirmed root cause and traverse downstream. With MCP, use
   `get_lineage(urn=<ROOT_URN>, upstream=False, max_hops=3)` and paginate if results are capped.
2. Include datasets, charts, dashboards, data jobs, and ML assets that the deployment returns.
   Deduplicate diamonds by URN while preserving the shortest hop count.
3. Rank dataset impact with usage statistics. For charts and dashboards lacking a usable OSS
   usage aspect, label any custom audience property as an estimate or seeded value rather than a
   native usage metric.
4. Resolve owners in a batch. Separate directly owned assets from ownerless consumers, and identify
   the root-cause owners plus owners of the highest-impact downstream assets.
5. Present the causal path, totals by entity type, ranked assets, owners, and evidence gaps before
   proposing writes.

---

## Step 6: Propose and Execute Approved Actions

Show an action plan and obtain explicit approval before any write. The plan should name exact
resources and include:

- Raise or reuse a DataHub incident on the symptom dataset with the root cause in its title
- Tag the root-cause dataset and implicated column, plus the supported impacted assets
- Notify root-cause owners and owners of the highest-impact consumers with the causal chain
- Leave the incident in investigation while human remediation remains outstanding

Check deployment capabilities before executing. Introspect GraphQL rather than guessing mutation
names or input types. Use `raiseIncident` when supported, and verify the returned incident URN.
Never claim that metadata actions repaired warehouse data.

If one write fails, stop mutation work, report which actions succeeded and failed, and ask how to
proceed. Never expand the target set beyond the approved scope.

---

## Step 7: Learn and Verify

After root-cause confirmation and approved action execution:

1. Write a compact structured post-mortem to a searchable dataset property. Include incident ID,
   symptom and root-cause URNs, measured evidence, causal path, ranked blast radius, human
   remediation, prevention, recalled incident IDs, detection time, and confidence.
2. Write the full Markdown narrative as a DataHub Document when supported, relate it to the root
   cause and symptom, and add an institutional-memory link from the root-cause dataset.
3. Merge summary custom properties; do not replace unrelated properties.
4. Re-read the incident, tags, column tag, structured property, Document by URN, link, and merged
   properties. Search-backed reads may lag, so distinguish immediate aspect verification from
   eventual indexing.
5. End with what broke, why, who is affected, what was written, and exactly what a human must do.

The structured property is the recall index. Do not make recall depend on Document search, which
may be unavailable on OSS.

---

## Reference Documents

| Document              | Path                                            | Purpose                                                             |
| --------------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| DataHub CLI reference | `../shared-references/datahub-cli-reference.md` | CLI, MCP, GraphQL, and entity syntax in the upstream registry       |
| DataHub Search skill  | `/datahub-search`                               | Entity resolution, metadata lookup, and ownership questions         |
| DataHub Lineage skill | `/datahub-lineage`                              | General traversal, path mapping, and non-incident impact analysis   |
| DataHub Quality skill | `/datahub-quality`                              | Assertion, incident, and subscription management by deployment tier |

---

## Common Mistakes

- **Calling MCP lineage with `direction=`.** MCP `get_lineage` takes `upstream: bool`; use
  `upstream=True` for ancestors and `upstream=False` for dependents.
- **Using an invalid hop depth.** MCP `max_hops` accepts `1`, `2`, or `3+`; use one hop during RCA
  and a bounded transitive call for impact analysis.
- **Calling `get_dataset_assertions` against OSS.** It is Cloud-only. Read dataset health and
  assertion details through GraphQL on OSS.
- **Trusting `hasFailingAssertions`.** It is unreliable on known OSS builds. Use `Dataset.health`
  as the failing-signal source and inspect `causes` for assertion URNs.
- **Trusting timeseries response order.** Operations, profiles, usage, and assertion events can be
  order-unstable; `limit` can truncate before ordering. Request a safe window and select the
  greatest `timestampMillis` yourself.
- **Stopping at the first broken ancestor.** A broken intermediate can inherit its failure from an
  unhealthy parent. Apply the stop rule before naming root cause.
- **Treating memory as proof.** Recalled post-mortems must be checked against live evidence.
- **Replacing custom properties.** Merge patch them so catalog metadata is not clobbered.
- **Skipping approval or verification.** Show the write plan, obtain approval, then re-read every
  artifact.

---

## Red Flags

- User input contains shell metacharacters → reject it; do not pass it to the CLI.
- The candidate cause still has an unhealthy parent → continue upstream.
- Recall conflicts with current evidence → discard the recalled hypothesis and run a cold walk.
- Lineage returns zero edges but ingestion completeness is unknown → report an evidence gap, not
  “no dependencies.”
- A write targets an entity outside the approved incident scope → refuse it.
- The deployment tier is unknown and the requested mutation may be Cloud-only → inspect or ask
  before proposing execution.
- A notification has no resolved owner or a ranking has no usage basis → label the gap explicitly.

---

## Remember

- Recall first, then verify.
- Walk upstream one hop at a time and stop only on intrinsic failure.
- Follow column lineage when the signal identifies a field.
- Rank downstream impact with measured catalog evidence and label estimates.
- Get explicit approval before writes and never claim metadata repaired data.
- Preserve a searchable structured post-mortem so the next incident is cheaper.
