# Migration Plan: `<column>` on `<entity>`

**Migration ID:** `<id>`
**What's changing:** `<retype | rename | deprecate-and-replace>`
**Old:** `<old_name>` (`<old_type>`)
**New:** `<new_name>` (`<new_type>`)
**Sunset window:** `<days>` days after contract

## Why

<One paragraph: what's wrong with the current state, why this change,
why now.>

## Blast radius

| Consumer | Entity type | Needs a code change? | Why / why not |
| -------- | ----------- | --------------------- | -------------- |
| | | | |

## Plan

1. **Expand:** `<the additive DDL, in words or SQL>`
2. **Migrate:** `<N>` PRs, in this order:
   - `<consumer 1>` (depends on: `<target>`)
   - `<consumer 2>` (depends on: `<consumer 1>`)
3. **Verify:** chained parallel-run per consumer, key column(s) and
   tolerance:

   | Consumer | Key column(s) | Value column | Tolerance |
   | -------- | ------------- | ------------ | --------- |
   | | | | |

4. **Contract:** deprecate `<old_name>` with sunset `<date>`, replacement
   pointer `<new_name>`.

## Verification results

| Consumer | Rows compared | Result |
| -------- | ------------- | ------ |
| | | |

## PRs opened

- `<link>` -- `<consumer>`

## For a sibling migration

<What would carry over directly if this same pattern is applied to a
related column later -- lineage shape, verification design, anything
that surprised you this time.>
