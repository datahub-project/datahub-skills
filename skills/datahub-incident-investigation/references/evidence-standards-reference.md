# Evidence Standards Reference

How to decide whether you actually know something during a data incident investigation. Used by `datahub-incident-investigation`.

The core discipline: **facts come only from tool output, and every claim carries the ID of the result it came from.** An investigation report where the reader cannot trace a number back to a command is a narrative, not a postmortem.

---

## Evidence Taxonomy

Assign every tool result an ID (`[E1]`, `[E2]`, …) at the moment you get it, along with its class. Classes matter because the confirmation gate requires specific ones.

| Class              | Source                                        | Establishes                                      | Cannot establish                           |
| ------------------ | --------------------------------------------- | ------------------------------------------------ | ------------------------------------------ |
| **Metadata**       | `datahub get`, `datahub graphql` entity reads | The contract, ownership, tags, custom properties | What the data actually contains            |
| **Lineage**        | `datahub lineage`                             | That a path exists between two assets            | That data flowed _wrongly_ along that path |
| **Change history** | `datahub timeline`, `git log`, `git diff`     | That something changed, and exactly when         | That the change caused the symptom         |
| **Quantitative**   | Warehouse profiles, baseline comparisons      | Magnitude, distribution, onset, cohort isolation | Intent, or why the values are wrong        |
| **Semantic**       | Observed values compared to the contract      | That values violate their documented meaning     | Which upstream introduced the violation    |
| **Verification**   | Test suites, assertion runs, re-measurement   | That a state is currently healthy or broken      | That the fix was the right fix             |

**The two classes people confuse.** Metadata is not quantitative evidence: a field description saying "in whole seconds" proves the contract, never the contents. Lineage is not causal evidence: an edge proves reachability, never fault.

---

## Recording an Evidence Item

Keep a running list. Each entry needs enough to re-run:

```markdown
### [E4] Segmented profile — stg_events.duration_ms by source_system

**Class:** Quantitative
**Command:** profiling SQL, `stg_events`, column `duration_ms`, segmented by `source_system`, 14 periods
**Key numbers:** `feed_c` mean = 4,187.2 from 2026-07-28 onward; all other segments mean 41.9 (ratio 99.9x).
`feed_c` mean before 2026-07-28 = 42.1.
**Supports:** H2 (unit change at the source)
**Eliminates:** H1 (duplicate rows — row counts flat across the window)
```

Three habits that make evidence hold up:

1. **Record the negative result too.** "Row counts are flat" eliminates an entire hypothesis class and costs one query.
2. **Record the baseline alongside the anomaly.** A number with nothing to compare against proves nothing.
3. **Never paraphrase upward.** If the profile says 99.9x, write 99.9x, not "roughly 100x" — the roundness may itself be the clue.

---

## The Two-Part Causal Test

A candidate cause must pass **both** tests. Most wrong conclusions come from checking only one.

### Necessity — is the symptom confined to what the candidate touches?

The symptom should appear in exactly the rows, periods, and segments the candidate affects, and be absent elsewhere.

| Observation                                                  | Verdict                                                    |
| ------------------------------------------------------------ | ---------------------------------------------------------- |
| Symptom present only in the candidate's cohort               | Necessity satisfied                                        |
| Symptom also present in cohorts the candidate does not touch | Not necessary — there is another cause, or a different one |
| Candidate's cohort looks healthy                             | Eliminated                                                 |

Segmentation is how you test necessity cheaply. Group the suspect column by the categorical dimension that separates producers (source system, vendor, region, tenant, pipeline run) and compare segments against each other in the same period.

### Sufficiency — do magnitude and onset reproduce the symptom?

| Dimension     | Requirement                                                                                | Failure mode                                     |
| ------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| **Magnitude** | The candidate's effect accounts for most of the deviation. State the fraction as a number. | "Directionally consistent" with 2% of the effect |
| **Onset**     | The candidate's first bad period is within one refresh interval of the symptom's onset.    | A change dated three weeks earlier               |

Work the arithmetic explicitly. If the symptom is a 41x inflation and the candidate segment is 100x inflated but represents 40% of volume, compute the blended effect and check it lands near 41x. Write that computation into the report — it is the most convincing paragraph you will produce.

---

## Distractors

A distractor is a **real** change that is not the cause. Naming the category is usually enough to eliminate it.

| Distractor type | Signature                                                     | One-command elimination                     |
| --------------- | ------------------------------------------------------------- | ------------------------------------------- |
| **Too small**   | Effect is orders of magnitude below the symptom               | Magnitude arithmetic                        |
| **Mis-dated**   | Landed outside the last-good → first-bad window               | `datahub timeline --start <LAST_GOOD_DATE>` |
| **Off-path**    | Real change, but never reaches the affected column            | `datahub lineage --column <COLUMN>`         |
| **Downstream**  | Consumes the defect rather than producing it                  | Direction check on the lineage traversal    |
| **Cosmetic**    | Documentation, tag, or ownership edit with no data effect     | `datahub timeline --category documentation` |
| **Sympathetic** | A second metric moved because it shares the same broken input | Trace both to a common upstream             |

**The most upstream rule.** When two assets on the same path both look wrong, the downstream one is a victim. Keep walking up until you reach an asset whose own inputs are healthy. That asset is the origin, and it is where the remediation belongs.

---

## The Confirmation Gate

Before declaring a root cause, check all five. If you would not pass this gate under review, you have a lead, not a cause.

| #   | Requirement                                                                 | Evidence class required        |
| --- | --------------------------------------------------------------------------- | ------------------------------ |
| 1   | A retrieved lineage path from the affected asset to the blamed asset        | Lineage                        |
| 2   | Quantitative evidence naming **both** the blamed asset and the blamed field | Quantitative                   |
| 3   | Magnitude accounting for most of the symptom, stated as a number            | Quantitative                   |
| 4   | Onset aligned within one refresh interval                                   | Quantitative or change history |
| 5   | At least one competing hypothesis eliminated with its own cited evidence    | Any                            |

Two failure modes this gate is designed to catch:

- **Blame by plausibility** — the story is coherent, but no profile ever measured the blamed field on the blamed asset.
- **Blame by proximity** — the asset one hop up is blamed because it was the first place anyone looked.

---

## Declaring No Incident

"The data is fine" needs the same standard of proof as a root cause, and is often the correct answer.

Require:

- Quantitative evidence showing the affected metric within its historical range for the reported period.
- An explanation of what the reporter actually observed — a different metric, a filtered view, a timezone boundary, a legitimate business event.
- Confirmation that no contract is being violated: the values still mean what the field documentation says they mean.

Benign changes that are **not** incidents: a new segment appearing in the data, a deliberate config or vendor migration that preserves semantics, a real demand spike, a backfill that restores previously missing rows.

---

## Semantic Failures

The failure class thresholds cannot see. Types validate, row counts are normal, freshness is current, nulls are absent — and every value is wrong.

| Pattern                      | What to compare                                                   | Telltale                                        |
| ---------------------------- | ----------------------------------------------------------------- | ----------------------------------------------- |
| **Unit or scale change**     | Segment means against each other, and against the documented unit | Ratio near a round factor (100, 1000, 60, 1024) |
| **Currency normalization**   | Values against the reference rate the contract specifies          | Ratio tracks a real exchange rate               |
| **Timezone shift**           | Period boundaries against the documented timezone                 | A constant offset in period assignment          |
| **Encoding or ID collision** | Distinct-count of a key against its expected cardinality          | Cardinality drops while row count holds         |
| **Silent default**           | Distribution of a field against its documented range              | A single value becomes implausibly frequent     |
| **Join fan-out**             | Row count at each stage of the path                               | Counts multiply at one specific hop             |

The general recipe: take the contract sentence from the field description, turn it into a comparison that would fail if the sentence were false, and run that comparison per segment.

---

## Verification Standards

A remediation is verified when **two independent** checks pass:

1. **The symptom measurement returns to its expected range.** Re-run the exact measurement from Step 1 and state the new value against the expected one.
2. **The full existing test or assertion suite still passes.** Not a subset — the whole thing. A repair that fixes the headline number and breaks three other checks is a failed repair.

Report both. If either fails, iterate on the remediation; do not stop at a failing state and do not narrow the suite to make it green.

Record the pre-repair and post-repair values side by side:

```markdown
| Check              | Before        | After         | Expected      |
| ------------------ | ------------- | ------------- | ------------- |
| Daily metric value | 4,187,204     | 41,872        | ~42,000       |
| Test suite         | 25/32 passing | 32/32 passing | 32/32 passing |
```
