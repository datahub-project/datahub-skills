# Investigation Ledger Entry — {{hunt_id}}

**Case:** {{case_name}}
**Run:** {{run_timestamp}}
**Status:** pending-review | confirmed | rejected

## Hypothesis

{{One falsifiable sentence. What would be true if the suspicion holds?}}

## Method

{{Technique + thresholds. e.g. "Weekly volume baseline over comm_edges;
flag weeks with z-score > 3.0 within 90 days of a restatement event."}}

## Evidence

| Artifact         | URN / location               |
| ---------------- | ---------------------------- |
| Evidence dataset | {{evidence_dataset_urn}}     |
| DataJob (SQL)    | {{datajob_urn}}              |
| Source datasets  | {{input_urns, one per line}} |

**Row count:** {{n}} — **Key rows:** {{2–3 rows that carry the finding}}

## Finding

{{What the evidence shows, stated conservatively. Distinguish "the data
shows X" from "X implies Y" — the second part is the reviewer's call.}}

## Governance notes

- Restricted data excluded: {{list or "none encountered"}}
- Assets tagged: {{risk-flagged / under-investigation URNs}}
- Glossary proposals: {{terms proposed, or "none"}}

## Review

| Field    | Value                    |
| -------- | ------------------------ |
| Verdict  | {{pending}}              |
| Reviewer | {{name}}                 |
| Date     | {{date}}                 |
| Note     | {{reviewer's rationale}} |
