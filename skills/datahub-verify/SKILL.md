---
name: datahub-verify
description: |
  Use this skill when an agent is about to propose data code, trust DataHub metadata, or select catalog assets for a broad query and needs an evidence-backed verification first. It calls Sidq's deterministic MCP checks to gate changes, compare catalog context with live sources, and distinguish verified, stale, unverified, unverifiable, and rejected assets. Triggers on: "verify before querying", "check this SQL", "is this asset trustworthy", "validate the catalog", "can I use this dataset", "check for PII exposure", or any request to propose data code against DataHub metadata.
user-invocable: true
allowed-tools: mcp__sidq__check_change, mcp__sidq__verify_context, mcp__sidq__search_verified
---

# DataHub Verify

You are an evidence-first DataHub verification specialist. Your role is to stop an agent from proposing data code on a refused change or silently trusting catalog metadata that disagrees with the live source. Verify what Sidq can verify, report what it cannot, and never turn an absent check into a clean result.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full verify-before-proposing and verify-before-trusting workflow
- All three Sidq MCP tools, and the separate `sidq verify` CLI receipt read
- Reading a decision, an abstention, and a receipt disposition

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**External dependency:** unlike the official catalog skills, this one calls a
separate MCP server (`sidq-mcp`) rather than the DataHub CLI. If that server is
not attached, the correct behaviour is to say verification did not run — never to
approximate a verdict from ordinary catalog search results.

---

## Not This Skill

| If the user wants to...             | Use this instead   |
| ----------------------------------- | ------------------ |
| Set up a connection                 | `/datahub-setup`   |
| Search or discover catalog entities | `/datahub-search`  |
| Explore lineage                     | `/datahub-lineage` |
| Update metadata                     | `/datahub-enrich`  |
| Manage assertions or incidents      | `/datahub-quality` |

Use this skill before those workflows when the question is whether the context is safe to rely on. Verification is a gate and an explanation, not a replacement for the catalog skills.

**Key boundary:** the catalog skills answer _what the catalog says_. This one answers _whether what it says is supported by evidence_ — and refuses on the user's behalf when it is not.

---

## Install

This skill installs the same way as every other skill here — copy it into your
project's skills directory, or use `npx skills add`:

```bash
cd /absolute/path/to/data-repository
npx skills add datahub-project/datahub-skills --skill datahub-verify --agent codex
```

Installing the skill does not install what it depends on. Unlike the catalog
skills, this one does not drive the DataHub CLI: it calls a separate MCP server,
[Sidq](https://github.com/NexuChat/sidq), which runs the deterministic checks and
holds the verification records. Sidq is Apache-2.0 and self-hosted, and the
section below connects it. If it is not attached, the correct behaviour is to
report that verification did not run.

---

## Connect the MCP server in Codex

The official `mcp-server-datahub` is Sidq's graph dependency. `sidq-mcp` is the
separate Sidq server that exposes the three tools used by this skill. From a
shell, register it with absolute paths:

```bash
codex mcp add sidq --env DATAHUB_GMS_URL=http://localhost:8080 --env SIDQ_REPO_ROOT=/absolute/path/to/data-repository -- /absolute/path/to/sidq/.venv/bin/sidq-mcp
codex mcp list
```

Start Codex and enter `/mcp` to verify that all three tools are active. Validate
the connected setup from the separate Sidq repository first:

```bash
cd /absolute/path/to/sidq
make mcp-smoke
```

Do not publish or store secret values. When a DataHub token or PostgreSQL DSN is
needed, export it in the shell that launches Codex and forward its name from a
trusted repository's `.codex/config.toml`:

```toml
[mcp_servers.sidq]
command = "/absolute/path/to/sidq/.venv/bin/sidq-mcp"
cwd = "/absolute/path/to/data-repository"
env_vars = ["DATAHUB_GMS_TOKEN", "SIDQ_POSTGRES_DSN"]

[mcp_servers.sidq.env]
DATAHUB_GMS_URL = "http://localhost:8080"
SIDQ_REPO_ROOT = "/absolute/path/to/data-repository"
```

`SIDQ_POSTGRES_DSN` enables the live PostgreSQL `schema_drift` check. If it is absent, that check belongs in `unverifiable`. If the repository has more than one manifest model, set `SIDQ_SQL_PATH` to the model used by raw SQL calls. Verification history defaults to `$SIDQ_REPO_ROOT/.sidq/mcp-verifications.json`; `SIDQ_VERIFICATION_STORE` can override it.

If the MCP tools are not available, say that verification could not be performed. Do not simulate a verdict from ordinary DataHub search results.

---

## Verify before proposing data code

Before writing or proposing SQL, call `check_change` with exactly one argument:

- `sql`: the complete proposed SQL for the sole manifest model, or the model selected by `SIDQ_SQL_PATH`.
- `diff`: a unified diff containing one or more changed, manifest-mapped SQL files.

```json
{
  "name": "check_change",
  "arguments": {
    "sql": "select customer_id, email from raw.customers"
  }
}
```

Read the returned `decision` as policy, not as a suggestion:

- `PASS`: the deterministic checks found no blocking policy finding. You may explain the evidence and continue.
- `WARN`: the proposal is not blocked, but name each warning and ask whether the user wants to proceed.
- `BLOCK`: do not propose or endorse the refused code. Explain the returned finding's `rule_id`, `message`, `severity`, and relevant evidence. Offer a compliant alternative, such as removing an unapproved field, changing the scope, or requesting the required governance change.

Never weaken a `BLOCK` into a warning, retry until it passes, or invent an exception. A graph failure is an explicit `GRAPH_UNAVAILABLE` failure and does not grant permission.

### Worked example: blocked cross-team downstream change

The repository example `examples/01-blocked-pii-dashboard/verdict.json` is an actual Sidq verdict. Removing `cust_email` is blocked by `critical_downstream` because the proven blast evidence contains cross-team owners. `wide_blast_radius` records 16 consumers as a WARN. The downstream `PII_Data` tag is sensitivity context; this removal does not emit `pii_exposure`.

```json
{
  "commit_sha": "5addb753788935d4d1aa6a9483c28c6fc124e5c7",
  "decision": "BLOCK",
  "findings": [
    {
      "evidence": [
        {
          "detail": {
            "downstream_count": 16
          },
          "graph_links": [
            "https://datahub.mlki.app/dataset/urn%3Ali%3Adataset%3A%28urn%3Ali%3AdataPlatform%3Adbt%2Cb2fd91.order_entry_db.order_entry.customers%2CPROD%29"
          ],
          "kind": "blast_radius",
          "subject": "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD)"
        }
      ],
      "message": "This change affects 16 downstream consumers for urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD).",
      "rule_id": "wide_blast_radius",
      "severity": "warn"
    },
    {
      "evidence": [
        {
          "detail": {
            "cross_team_owners": [
              "urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2",
              "urn:li:corpGroup:b2fd91.ORG_BACKEND_ENG",
              "urn:li:corpuser:b2fd91.alex@example.com",
              "urn:li:corpuser:b2fd91.brock1@example.com",
              "urn:li:corpuser:b2fd91.bryan@example.com",
              "urn:li:corpuser:b2fd91.jonny2@example.com",
              "urn:li:corpuser:b2fd91.kirk@example.com",
              "urn:li:corpuser:b2fd91.marty@example.com",
              "urn:li:corpuser:b2fd91.sam@example.com"
            ]
          },
          "graph_links": [
            "https://datahub.mlki.app/dataset/urn%3Ali%3Adataset%3A%28urn%3Ali%3AdataPlatform%3Adbt%2Cb2fd91.order_entry_db.order_entry.customers%2CPROD%29"
          ],
          "kind": "blast_radius",
          "subject": "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD)"
        }
      ],
      "message": "This change has critical or cross-team downstream consumers for urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD).",
      "rule_id": "critical_downstream",
      "severity": "block"
    }
  ],
  "policy_hash": "66f48004804c5ce02955699710466b6d58ae7a868f876a4774e548c5c15920b8"
}
```

Tell the user that `critical_downstream` is the blocking rule and name the cross-team owner evidence. Do not present the 16-consumer warning or the PII tag as the blocking cause. A compliant next step must preserve compatibility for the verified downstream consumers or obtain an explicit governance decision.

---

## Verify before trusting an asset

Before relying on catalog schema, lineage, or metadata for an asset, call `verify_context` with its dataset URN:

```json
{
  "name": "verify_context",
  "arguments": {
    "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.customers,PROD)"
  }
}
```

`truthful: true` means every truth check that Sidq required for that asset completed without findings. If `truthful` is false, inspect `findings` and say plainly what disagrees. For example, `lineage_rot_missing` means the catalog claims a column edge that the available model SQL does not reproduce; do not silently use the catalog lineage as if it were current.

If a live source, model SQL, column-level lineage, or constraint introspection is missing, report the named item in `unverifiable`. Sidq currently checks `schema_drift` (catalog schema versus live PostgreSQL), `lineage_rot` (stored column lineage versus local model SQL), and `constraint_reconciliation` (catalog constraint claims versus the constraints the source enforces). `lineage_rot` cannot be adjudicated without model SQL. Do not claim any check passed when it was not run.

Read `constraint_contradicts_catalog` precisely: the catalog claimed a constraint the live source does not enforce, so a query that relies on that guarantee may be wrong. The reverse — the source enforcing something the catalog never mentioned — is deliberately not reported as a truth finding, because the catalog is silent rather than untruthful, and the schema aspect cannot express keys or check constraints at all. Do not present catalog silence to a user as a catalog lie.

Example response to explain:

```json
{
  "checked_at": "2026-07-28T12:00:00Z",
  "truthful": false,
  "findings": [
    {
      "kind": "lineage_rot_missing",
      "subject": "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.customers,PROD)#email"
    }
  ],
  "unverifiable": [],
  "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.customers,PROD)"
}
```

Say: “The catalog is not truthful for this asset: its stored `email` lineage is not produced by the available model SQL.” Then pause or ask the user whether to proceed with an explicitly unverified source. Do not hide the disagreement behind a generic “lineage available” statement.

---

## Query broadly only from verified assets

When selecting assets for analysis, generated SQL, or a broad question, prefer `search_verified`:

This tool classifies matches from the Sidq MCP verification store and reports
`verification_source: sidq_mcp_store`. It is not a DataHub Receipt reader; the
independent Receipt consumer is the separate `sidq verify <urn>` CLI path.

```json
{
  "name": "search_verified",
  "arguments": {
    "query": "customers",
    "max_age_days": 7
  }
}
```

Use only the `verified` list by default. The categories are materially different:

| Result         | Meaning                                                  | Default action                                                    |
| -------------- | -------------------------------------------------------- | ----------------------------------------------------------------- |
| `verified`     | Truthful evidence exists within the requested age window | Safe candidate for the next step, subject to normal policy checks |
| `unverified`   | Never checked                                            | Do not treat as clean; verify it first                            |
| `stale`        | Checked, but outside `max_age_days`                      | Re-verify before relying on it                                    |
| `unverifiable` | A required truth check could not complete                | Report the missing evidence; do not promote it to verified        |
| `rejected`     | Checked within the window and found untruthful           | Exclude it unless the user explicitly addresses the finding       |

“Never verified” is not the same as “verified clean.” If DataHub search itself fails and the response contains `error.code: "GRAPH_UNAVAILABLE"`, treat the operation as failed, not as an empty search result.

---

## Read a verdict and its receipt

Sidq separates deterministic evidence from advisory interpretation:

- Deterministic checks and policy findings are the only findings that can produce `BLOCK`.
- Advisory findings may describe semantic or model-assisted concerns, but they can only produce `WARN`; they can never turn `PASS` into `BLOCK`.
- A verdict's `policy_hash` identifies the policy used. Its `commit_sha` identifies the resolved code state. Together they let another agent reproduce the same decision from the same inputs, policy, and commit.
- A receipt can go stale. The live schema, model SQL, DataHub graph, policy, or verification age can change after it was issued. Treat `checked_at` and the requested `max_age_days` as part of the evidence, not as decoration. Re-run the check when the receipt is outside the freshness window or the inputs changed.

Do not describe `policy_hash` + `commit_sha` as proof that the world is unchanged. They make the verdict reproducible for the captured inputs; they do not freeze the catalog or source.

---

## Read a persisted Receipt written into DataHub

`search_verified` reads Sidq's own MCP verification store. A **Receipt** is different: it is written into DataHub as `sidq.*` structured properties by an explicit opt-in writeback, and any process can read it back. That read is the `sidq verify <urn>` CLI, not an MCP tool:

```bash
sidq verify 'urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.customers,PROD)' --json
```

It answers three separate questions, and collapsing them is the mistake this section exists to prevent:

| Field           | Question                                           | Values                                                 |
| --------------- | -------------------------------------------------- | ------------------------------------------------------ |
| `receipt_state` | Does the receipt still apply?                      | `CURRENT` · `STALE` · `ABSENT` · `INVALID`             |
| `verdict`       | What did the engine decide?                        | `PASS` · `WARN` · `BLOCK`                              |
| `action`        | What may you do?                                   | `CONTINUE` · `REVIEW_OR_ESCALATE` · `STOP` · `RECHECK` |
| `covers_asset`  | Was the asset examined under conditions that hold? | `true` · `false`                                       |

Act on `action`, and only on `action`:

| Headline                                      | What it means                               | Do this                                            |
| --------------------------------------------- | ------------------------------------------- | -------------------------------------------------- |
| `CURRENT RECEIPT · PASS · CONTINUE`           | Checked, and nothing blocking was found     | Proceed, and say what the receipt rests on         |
| `CURRENT RECEIPT · WARN · REVIEW_OR_ESCALATE` | Checked, with a named concern               | Name the warning and ask before proceeding         |
| `CURRENT RECEIPT · BLOCK · STOP`              | Checked, and **refused**                    | Stop. This is the most examined an asset ever is   |
| `NOT VERIFIED`                                | Absent, stale, or unreadable — nobody knows | Say so plainly, then re-check. Never call it clean |

Two rules follow, and neither is optional:

- **A refusal is not an absence.** `CURRENT RECEIPT · BLOCK · STOP` means the check ran and said no. Reporting it as unverified would understate it; reporting it as verified would invert it.
- **Coverage is not permission.** A current `BLOCK` covers the asset — a bounded audit is right to move on rather than re-refuse it — but it authorizes nothing. Only `CONTINUE` does.

Exit codes follow `action`: `0` for `CONTINUE` and `REVIEW_OR_ESCALATE`, `1` for `STOP` and `RECHECK`, and `2` when the catalog could not be read at all. `STOP` and `RECHECK` share an exit code because stopping is the only safe move in both cases — read the headline to tell them apart.

---

## Common Mistakes

- **Proposing before `check_change`.** Stop and run the gate first.
- **Continuing after `BLOCK`.** Explain the named rule and offer a compliant alternative.
- **Treating DataHub metadata as ground truth.** Run `verify_context(urn)` before relying on it.
- **Calling an unverified result clean.** Distinguish `unverified`, `stale`, `unverifiable`, and `rejected`.
- **Claiming checks Sidq cannot run.** State when model SQL or a live source is missing.
- **Treating a stale receipt as current.** Re-run verification after the freshness window or any relevant input change.
- **Reporting a current `BLOCK` as `NOT VERIFIED`.** A refusal was checked. `NOT VERIFIED` is reserved for absent, stale, and unreadable receipts.
- **Reading `covers_asset` as permission.** It answers whether the asset was examined, not whether you may act.

## Red Flags

- **The Sidq MCP tools are not attached** → say verification could not be performed. Do not substitute catalog search results for a verdict.
- **A response carries `error.code: "GRAPH_UNAVAILABLE"`** → the operation failed. It is not an empty result, and it does not grant permission.
- **A `BLOCK` you are tempted to re-run with different wording** → stop. Retrying until a gate passes is circumventing it.
- **`unverifiable` is non-empty and you are about to summarise "checks passed"** → name each item that could not be checked instead.
- **The user asks you to proceed anyway after a `BLOCK`** → that is their call to make explicitly, and it belongs in the record. State the rule you are overriding by name.

## Remember

Verify before you propose. Verify before you trust. Use verified search for broad selection. Explain refusals by their named rule. Report abstentions plainly.
