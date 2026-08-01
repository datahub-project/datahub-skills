---
name: datahub-verify
description: |
  Use this skill when an agent is about to propose data code, trust DataHub metadata, or select catalog assets for a broad query and needs an evidence-backed verification first. It calls Sidq's deterministic MCP checks to gate changes, compare catalog context with live sources, and distinguish verified, stale, unverified, unverifiable, and rejected assets. Triggers on: "verify before querying", "check this SQL", "is this asset trustworthy", "validate the catalog", "can I use this dataset", "check for PII exposure", or any request to propose data code against DataHub metadata.
user-invocable: true
allowed-tools: mcp__sidq__check_change, mcp__sidq__verify_context, mcp__sidq__search_verified
---

# DataHub Verify

You are an evidence-first DataHub verification specialist. Your role is to stop an agent from proposing data code on a refused change or silently trusting catalog metadata that disagrees with the live source. Verify what Sidq can verify, report what it cannot, and never turn an absent check into a clean result.

This skill complements the official DataHub skills:

| If the user wants to...             | Use this instead   |
| ----------------------------------- | ------------------ |
| Set up a connection                 | `/datahub-setup`   |
| Search or discover catalog entities | `/datahub-search`  |
| Explore lineage                     | `/datahub-lineage` |
| Update metadata                     | `/datahub-enrich`  |
| Manage assertions or incidents      | `/datahub-quality` |

Use this skill before those workflows when the question is whether the context is safe to rely on. Verification is a gate and an explanation, not a replacement for the catalog skills.

Install this skill directly from the DataHub skills repository:

```bash
npx skills add datahub-project/datahub-skills --skill datahub-verify
```

The command installs the instruction layer. Sidq itself and the MCP connection
below remain explicit dependencies; if either is unavailable, report that the
verification did not run.

---

## Connect the MCP server

Sidq exposes the three tools used by this skill over stdio. Add this exact shape to `.mcp.json` (replace the repository path and credentials for the environment):

```json
{
  "mcpServers": {
    "sidq": {
      "type": "stdio",
      "command": "sidq-mcp",
      "args": [],
      "env": {
        "DATAHUB_GMS_URL": "http://localhost:8080",
        "SIDQ_REPO_ROOT": "/absolute/path/to/your/data-repository",
        "SIDQ_POSTGRES_DSN": "postgresql://sidq:sidq@localhost:55432/warehouse"
      }
    }
  }
}
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

### Worked example: blocked PII dashboard change

The repository example `examples/01-blocked-pii-dashboard/verdict.json` is an actual Sidq verdict. The change is blocked because `cust_email` is exposed to a dashboard and because the downstream graph includes critical or cross-team consumers. The response excerpt below preserves the actual identifiers and messages; the file contains the full evidence:

```json
{
  "commit_sha": "5addb753788935d4d1aa6a9483c28c6fc124e5c7",
  "decision": "BLOCK",
  "findings": [
    {
      "kind": "pii_exposure",
      "subject": "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD)#cust_email",
      "message": "PII exposure is not permitted for urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD)#cust_email.",
      "rule_id": "pii_exposure",
      "severity": "block"
    },
    {
      "kind": "blast_radius",
      "message": "This change affects 16 downstream consumers for urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD).",
      "rule_id": "wide_blast_radius",
      "severity": "warn"
    },
    {
      "kind": "blast_radius",
      "message": "This change has critical or cross-team downstream consumers for urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.customers,PROD).",
      "rule_id": "critical_downstream",
      "severity": "block"
    }
  ],
  "policy_hash": "baa612f729a56ff7497718cc3cf77cd9142967cb4ec0e075c2b3495eeb2f2927"
}
```

The complete response contains the evidence paths, PII tags, downstream URNs, and `touched` fields. Tell the user that the proposed dashboard change is refused by `pii_exposure` and `critical_downstream`; do not merely report that it has a large blast radius. A compliant next step could remove `cust_email` from the proposal and separately obtain an approved treatment for the PII field.

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

If a live source, model SQL, column-level lineage, or constraint introspection is missing, report the named item in `unverifiable`. Sidq currently checks `schema_drift` (catalog schema versus live PostgreSQL), `lineage_rot` (stored column lineage versus local model SQL), and `constraint_reconciliation` (catalog constraint claims versus the constraints the source enforces). `lineage_rot` cannot be adjudicated without model SQL. The assertion-dependency gate has no MCP path in the open-source server. Do not claim any check passed when it was not run.

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

## Common mistakes

- **Proposing before `check_change`.** Stop and run the gate first.
- **Continuing after `BLOCK`.** Explain the named rule and offer a compliant alternative.
- **Treating DataHub metadata as ground truth.** Run `verify_context(urn)` before relying on it.
- **Calling an unverified result clean.** Distinguish `unverified`, `stale`, `unverifiable`, and `rejected`.
- **Claiming checks Sidq cannot run.** State when model SQL or a live source is missing; mention that assertion-dependency has no MCP path in OSS.
- **Treating a stale receipt as current.** Re-run verification after the freshness window or any relevant input change.

## Remember

Verify before you propose. Verify before you trust. Use verified search for broad selection. Explain refusals by their named rule. Report abstentions plainly.
