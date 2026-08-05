# Economics Report

## Scope

**Assets priced:** <!-- count -->
**Scope:** <!-- platform / domain / container / URN list -->
**Observation window:** <!-- e.g. 30 days, 2026-01-01 to 2026-01-31 -->

## Rate Card

| Rate           | Value               | Source                           |
| -------------- | ------------------- | -------------------------------- |
| Storage        | <!-- $/TB-month --> | <!-- contract or vendor list --> |
| Compute        | <!-- $/TB -->       | <!-- contract or vendor list --> |
| Terminal value | <!-- $/day -->      | <!-- user-supplied or proxy -->  |

<!-- If source is vendor list price, say so here and note that the org's contract is likely cheaper, making every figure an upper bound. -->

## Where the Money Goes

| Component       | Annual USD | Share      |
| --------------- | ---------- | ---------- |
| Storage         | <!-- $ --> | <!-- % --> |
| Read compute    | <!-- $ --> | <!-- % --> |
| Rebuild compute | <!-- $ --> | <!-- % --> |
| **Total**       | <!-- $ --> | 100%       |

**Recoverable per year:** <!-- storage + rebuild on DEAD_WEIGHT assets only -->
**Value at risk per day:** <!-- sum over distinct terminals -->

## Verdicts

| Verdict        | Assets     | Annual cost | Recoverable/yr |
| -------------- | ---------- | ----------- | -------------- |
| `LOAD_BEARING` | <!-- n --> | <!-- $ -->  | —              |
| `HEALTHY`      | <!-- n --> | <!-- $ -->  | —              |
| `OVERSERVED`   | <!-- n --> | <!-- $ -->  | <!-- $ -->     |
| `DEAD_WEIGHT`  | <!-- n --> | <!-- $ -->  | <!-- $ -->     |
| `ORPHANED`     | <!-- n --> | <!-- $ -->  | —              |
| `UNPRICEABLE`  | <!-- n --> | —           | —              |

## Findings

<!-- One block per asset, highest recoverable or highest value at risk first.
     Every block carries counter-evidence on a "−" line. -->

```text
<VERDICT>   <recover $X/yr | at risk $X/day>   <asset name>
  + <supporting evidence>
  + <supporting evidence>
  − <counter-evidence — what would make this recommendation wrong>
  confidence <0-1> — <what would raise it>
```

## Right-Sizing Candidates

<!-- OVERSERVED assets only. These are NOT deprecation candidates — they have live consumers. -->

| Asset         | Current cadence | Reads/day  | Target cadence | Saving/yr  |
| ------------- | --------------- | ---------- | -------------- | ---------- |
| <!-- name --> | <!-- n/day -->  | <!-- n --> | <!-- n/day --> | <!-- $ --> |

## Deprecation Candidates

<!-- DEAD_WEIGHT only. Quote recoverable (storage + rebuild), never total cost. -->

| Asset         | Queries in window | Reachable terminals | Recoverable/yr | Confidence   |
| ------------- | ----------------- | ------------------- | -------------- | ------------ |
| <!-- name --> | 0                 | 0                   | <!-- $ -->     | <!-- 0-1 --> |

## Unpriceable

| Asset         | Missing signal  | What would fix it                   |
| ------------- | --------------- | ----------------------------------- |
| <!-- name --> | <!-- aspect --> | <!-- ingestion source to enable --> |

## Assumptions

- **Hard dependency** — a failure exposes everything reachable downstream.
- **No distance decay** — a terminal five hops away counts the same as one hop away.
- **Terminals deduplicated** — each distinct endpoint counted exactly once.
- <!-- Read cost basis: full scan, or column-pruned via fieldCounts -->
- <!-- Any traversal caps hit, and which figures are therefore lower bounds -->

## Next Steps

1. <!-- e.g. right-size the top overserved assets -->
2. <!-- e.g. confirm the deprecation candidates with their owners, then use /datahub-enrich -->
3. <!-- e.g. enable usage ingestion on <platform> to price the unpriceable set -->
