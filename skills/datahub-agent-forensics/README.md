# DataHub Agent Forensics

Investigate what evidence and actions influenced an AI-agent decision, whether its
receipt is intact, and whether later DataHub changes made the output stale or unsafe
to replay.

## What it does

1. Resolves a receipt, run, incident, campaign, field, or output to exact identifiers
2. Uses DataHub MCP tools or CLI for discovery and direct entity retrieval
3. Uses an optional read-only evidence provider for receipt verification, recorded
   influence, deterministic prospective impact, and persisted worker findings
4. Separates generic lineage from run-specific influence evidence
5. Verifies signed receipts when a deterministic verifier is available
6. Classifies impact only through a versioned deterministic policy
7. Produces a raw-free forensic report with explicit limitations

## Capabilities

- **Decision causality** — What evidence and actions produced this output?
- **Reverse decision lineage** — Which prior agent outputs used this field?
- **Continuing validity** — Did this incident make the decision stale or at risk?
- **Approval binding** — Does an approval cover the exact action and resource set?
- **Replay safety** — Can a read-only replay be planned without rewriting history?

## Usage

```text
/catalog-agent-forensics why is receipt receipt:sha256:... stale?
/catalog-agent-forensics which agent decisions used the revenue field?
/catalog-agent-forensics was this action approved for the exact payload digest?
/catalog-agent-forensics can this decision be replayed read-only?
```

The skill is read-only by default. It never treats DataHub search, generic lineage,
or a Document projection as cryptographic proof.

An external evidence provider is optional. When one is connected, inspect its tool
schemas and prefer read-only capabilities for receipt verification, recorded
influence, deterministic impact, and persisted campaign findings. It complements
DataHub's catalog tools and must not be treated as mutation or replay authority.
