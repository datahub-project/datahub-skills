# Hypothesis Ledger: {incident_title}

Live working document for an in-flight investigation. Update it as evidence arrives; never delete a row — eliminated hypotheses are part of the postmortem.

**Affected asset:** {affected_asset_name} (`{affected_asset_urn}`)
**Last updated:** {timestamp}

---

## Symptom Statement

> {verbatim_symptom_statement}

| Element    | Value              |
| ---------- | ------------------ |
| Observable | {affected_field}   |
| Expected   | {expected_value}   |
| Observed   | {observed_value}   |
| Deviation  | {deviation}        |
| Last good  | {last_good_period} |
| First bad  | {first_bad_period} |

Every hypothesis below must explain **this** statement. If a candidate explains a different symptom, it is a separate finding.

---

## Suspect Set

From lineage traversal — do not add assets that traversal did not return.

| Hop | Asset        | Platform   | Feeds affected column? | Owner   | Health   |
| --- | ------------ | ---------- | ---------------------- | ------- | -------- |
| {n} | {asset_name} | {platform} | {yes_no}               | {owner} | {health} |

---

## Hypotheses

Status: `proposed` → `investigating` → `eliminated` / `confirmed`

| #   | Hypothesis                                                | Class           | Target asset   | Status   | Confidence   | Necessary? | Sufficient? | Evidence       |
| --- | --------------------------------------------------------- | --------------- | -------------- | -------- | ------------ | ---------- | ----------- | -------------- |
| H1  | {hypothesis}                                              | {class}         | {target_asset} | {status} | {confidence} | {verdict}  | {verdict}   | {evidence_ids} |
| H2  | {hypothesis}                                              | {class}         | {target_asset} | {status} | {confidence} | {verdict}  | {verdict}   | {evidence_ids} |
| H0  | Not an incident — the movement is real business behaviour | Not an incident | —              | {status} | {confidence} | —          | —           | {evidence_ids} |

Classes: source change, volume change, transform change, contract drift, schema change, late/partial data, not an incident.

**Keep H0 open until it is eliminated with evidence.** Inventing an incident is a worse failure than finding none.

---

## Evidence Log

| ID   | Class   | Command / query | Key numbers   | Supports   | Eliminates   |
| ---- | ------- | --------------- | ------------- | ---------- | ------------ |
| [E1] | {class} | {command}       | {key_numbers} | {supports} | {eliminates} |

Classes: metadata, lineage, change history, quantitative, semantic, verification.

Record baselines alongside anomalies, and record negative results — a flat row count eliminates a whole hypothesis class for one query.

---

## Eliminated Distractors

| Change observed | Distractor type | Why it is not the cause | Evidence       |
| --------------- | --------------- | ----------------------- | -------------- |
| {change}        | {type}          | {reason}                | {evidence_ids} |

Types: too small, mis-dated, off-path, downstream, cosmetic, sympathetic.

---

## Confirmation Gate

Do not declare a root cause until all five are checked.

| #   | Requirement                                                        | Met?  | Evidence       |
| --- | ------------------------------------------------------------------ | ----- | -------------- |
| 1   | Retrieved lineage path from affected asset to blamed asset         | {y_n} | {evidence_ids} |
| 2   | Quantitative evidence naming the blamed asset **and** blamed field | {y_n} | {evidence_ids} |
| 3   | Magnitude accounts for most of the symptom, stated as a number     | {y_n} | {evidence_ids} |
| 4   | Onset aligned within one refresh interval                          | {y_n} | {evidence_ids} |
| 5   | At least one competing hypothesis eliminated with cited evidence   | {y_n} | {evidence_ids} |

---

## Open Questions

- {question}

## Next Actions

| Action   | Cost   | Which hypothesis it tests |
| -------- | ------ | ------------------------- |
| {action} | {cost} | {hypothesis_id}           |

Attack cheapest-first: change history is free, metadata is cheap, a single segmented profile usually beats five targeted queries.
