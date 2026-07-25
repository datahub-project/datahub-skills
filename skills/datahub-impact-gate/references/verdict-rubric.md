# Verdict Rubric Reference

How the gate turns a change classification plus a blast radius into a PASS / REVIEW / BLOCK recommendation. When signals conflict, the **most conservative** verdict wins: BLOCK > REVIEW > PASS.

## Inputs to the decision

1. **Change classification** (per changed field, from Step 1 of the skill):
   - Breaking: column dropped, column renamed, incompatible type change (narrowing / cast-unsafe).
   - Non-breaking: column added, compatible type widening.
   - Unknown → treated as **breaking**.
2. **Blast radius** (from skip-cache `searchAcrossLineage`): the set of downstream `MLMODEL` and `DASHBOARD` entities, each with hop distance and owner(s).
3. **Confidence**: whether the lineage read was fresh (`skipCache: true`) and complete, and whether impacted entities have owners.

## The rubric

### BLOCK

- Any **breaking** change to a field on a dataset that feeds **≥ 1 ML model or dashboard**, **or**
- Any **breaking** change where the lineage read is ambiguous or cannot be confirmed fresh.

Merging risks silently corrupting a production consumer — a model training or scoring on missing/miscast data, or a dashboard reading a column that no longer exists.

### REVIEW

- Downstream models or dashboards exist, but the change is **additive** or a **compatible widening**, **or**
- The impacted consumers are **non-production** (e.g. `env` other than `PROD`), **unowned**, or only **partially confirmed** by lineage.

A human owner should sign off. REVIEW is the honest verdict when there is real downstream surface but the change itself is not provably breaking.

### PASS

- **No** downstream ML models or dashboards, **and**
- The change is additive or a compatible type widening.

Nothing downstream can break. Still present the (empty) impacted set so the reader can see the gate looked.

## Fail-safe rules

These override the table above toward caution:

| Situation                                            | Action                                                                                                                                       |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Breaking change, but `total: 0` downstream           | Verify `skipCache: true` was set. If still empty → **REVIEW** with a "lineage may be incomplete or not yet ingested" caveat. **Never PASS.** |
| Change cannot be classified                          | Treat as **breaking**.                                                                                                                       |
| Impacted production model/dashboard has **no owner** | **Never PASS** — at least **REVIEW** (no one to sign off).                                                                                   |
| Lineage flagged stale / older than last ingestion    | Downgrade **PASS → REVIEW**.                                                                                                                 |
| User asks to override the verdict                    | Explain the rubric. The verdict follows the lineage, not the ask.                                                                            |

## Why "empty ≠ safe"

The most common way a naive gate fails is reading a cached empty lineage answer as "no consumers." GMS caches empty answers for minutes. A gate that PASSes on empty is worthless precisely when a change is new — which is always the case in a pull request. Hence: for a **breaking** change, empty means "prove freshness," not "safe." See `ml-lineage-traversal.md`, Gotcha 1.

## Worked examples

| Change                             | Downstream                               | Verdict | Reason                                                         |
| ---------------------------------- | ---------------------------------------- | ------- | -------------------------------------------------------------- |
| Drop `airport_fee` (DOUBLE)        | feature → `fare_predictor` (PROD, owned) | BLOCK   | Breaking change feeds a production model                       |
| Add `promo_code` (STRING)          | feature → `fare_predictor` (PROD)        | REVIEW  | Additive, but the dataset feeds a model — flag for sign-off    |
| Widen `trip_count` INT → BIGINT    | dashboard `Ops Daily` (owned)            | REVIEW  | Compatible widening with a live consumer                       |
| Rename `pickup_ts` → `pickup_time` | (none, skip-cache confirmed)             | REVIEW  | Breaking, but empty downstream — cannot PASS a breaking change |
| Add `notes` (STRING)               | (none)                                   | PASS    | Additive, nothing downstream                                   |
