# DataHub Drift Contract

Predict which downstream **report columns** break when an upstream column changes, classify how
bad it is, draft a data contract that would have caught it, and — with consent — write the finding
back into DataHub.

## What it does

1. Pins the proposed change: dataset, column, and change type (`dropped` / `renamed` / `retyped`)
2. Reads `upstreamLineage.fineGrainedLineages` and traverses it to the exact downstream columns
3. Classifies severity — `hard_break` for drop/rename, `silent_break` for a retype
4. Drafts an enforceable contract on the changed upstream column
5. On approval, writes tags, a `drift_status` structured property, and the contract back

## Capabilities

- **Column-precise impact** — "these three report fields miscompute", not "this table is affected"
- **Silent-break detection** — a retype keeps flowing and quietly produces wrong numbers; this is
  the failure mode that survives to production
- **Contract drafting** — grounded in the transform, so a divide-by-100 downstream pins the
  upstream scale
- **Write-back** — the finding lands on the affected columns so the next person inherits it

## Usage

```
/datahub-drift-contract what breaks if I retype collateral.haircut_pct from percent to fraction?
/datahub-drift-contract impact of dropping ledger.cash_balance on the margin report
/datahub-drift-contract propose a data contract for orders.currency_code
/datahub-drift-contract flag drift on the columns affected by renaming users.signup_ts
```

## When to use something else

`/datahub-lineage` is the right tool for "what depends on X" and for table-level impact. Reach for
this skill only when the user names a specific column change, needs the answer at column
granularity, and wants a contract or a write-back. See **Not This Skill** in `SKILL.md`.

## Requirements

- Write-back needs the MCP server running with `TOOLS_IS_MUTATION_ENABLED=true` (mutations are off
  by default)
- Tags and the `drift_status` structured property must be provisioned before they can be applied —
  `add_tags` fails on a label that does not exist yet
