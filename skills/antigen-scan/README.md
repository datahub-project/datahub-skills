# Antigen Scan

Find and remove prompt-injection payloads (OWASP LLM01) planted in DataHub catalog free-text — entity descriptions, column descriptions, and Knowledge-Base documents — and write the remediation back into the graph.

## What it does

1. Sweeps the catalog read-only via `search`, `get_entities`, `search_documents`, and `grep_documents`
2. Scores every free-text surface with a deterministic standard-library rule — no model call, no network
3. Prints the exact mutation plan (URN, tool, field, before → after) and writes nothing
4. Waits for explicit human approval
5. Removes the injected span, quarantine-tags the entity, stamps tamper-evidence hashes, and files a hash-only forensic incident document
6. Maps two-hop downstream reach through lineage, certifies the clean remainder, and re-scans to prove the control is standing

## Usage

```text
/catalog-injection-scan sweep the catalog for prompt injection
/catalog-injection-scan show me what a cure would write, don't apply it
/catalog-injection-scan which downstream assets read the poisoned customers table?
/catalog-injection-scan gate our metadata CI on this
```

Or ask naturally: "check our column descriptions for jailbreaks", "is this catalog safe for an agent to read?".

## What you should know before running it

- **Every mutating command is dry-run by default against a live catalog.** `--apply` is required to write, and `cure` calls 4 write-back tools per finding — which the plan prints as 6 individual writes, since the three structured properties are counted separately — and `certify` calls 2 per _clean_ entity.
- **A degraded sweep is not an all-clear.** An unreachable or misconfigured GMS returns an empty catalog that looks identical to a clean one, so the scan fails closed with exit code 2.
- **Where no fixture records the field's original text, remediation replaces the whole description.** Antigen never persists a recoverable payload, so the prior text is recoverable only from DataHub's own aspect version history.

## Requires

[Antigen](https://github.com/edycutjong/antigen) (Apache-2.0, Python 3.10+), a reachable DataHub instance, and — for the write path — a self-hosted `mcp-server-datahub` with `TOOLS_IS_MUTATION_ENABLED`, `SAVE_DOCUMENT_TOOL_ENABLED`, and `SAVE_DOCUMENT_RESTRICT_UPDATES=false`. Verified against DataHub GMS `v1.7.0`, `acryl-datahub 1.6.0.6`, `datahub-agent-context 1.6.0.17`.

`python -m antigen scan --offline` runs the whole workflow against an in-memory corpus double with no Docker and no keys.
