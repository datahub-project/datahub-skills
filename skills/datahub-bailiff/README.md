# DataHub Bailiff

Govern AI agents that read and write DataHub — register identity, gate mutations, examine catalog claims, propose instead of cold-mutate, and inherit verdicts.

## What it does

1. Registers agents with risk tier + tool allowlists
2. Denies unregistered / over-scope cold mutates
3. Cross-examines catalog claims against warehouse truth
4. Converts R1/R2 writes into proposals for human accept/reject
5. Writes verdicts back so the next agent inherits trustworthy context

## Usage

```
/datahub-bailiff
/datahub-bailiff should this agent be allowed to mutate?
/datahub-bailiff verify this description against SQL
/datahub-bailiff register a governed steward
```

Requires the [Bailiff](https://github.com/AmanM006/Bailiff) CLI/Court for the executable gate (`bailiff mcp`, `bailiff examine`, …).
