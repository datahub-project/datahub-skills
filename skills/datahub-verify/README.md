# datahub-verify

Evidence-first verification for DataHub-backed agents. It checks proposed data-code changes, compares catalog context with live sources, and keeps unverified or stale assets distinct from verified ones.

Install it from the root of the target data repository where Codex will start:

```bash
cd /absolute/path/to/data-repository
npx skills add NexuChat/sidq --skill datahub-verify --agent codex
```

The verified install location is
`/absolute/path/to/data-repository/.agents/skills/datahub-verify`. This command
does not install Sidq or attach MCP. Complete the Codex MCP setup in
[`../../docs/MCP-SERVER.md`](../../docs/MCP-SERVER.md), then validate it from the
separate Sidq repository root:

```bash
cd /absolute/path/to/sidq
make mcp-smoke
```

## What it does

- Calls `check_change` before an agent proposes SQL and honors `BLOCK` decisions.
- Calls `verify_context(urn)` before trusting an asset's catalog metadata.
- Uses `search_verified` for broad selection from the Sidq MCP verification store and preserves freshness and abstention states; this is distinct from DataHub Receipt reading via `sidq verify`.
- Explains deterministic versus advisory findings and reproducible, expiring receipts.

## Usage

```
> Verify this SQL before proposing it
> Is this DataHub dataset trustworthy right now?
> Find verified customer assets for a broad query
```

## Files

| File       | Purpose                                 |
| ---------- | --------------------------------------- |
| `SKILL.md` | Main verification workflow and examples |
