# Silent-Failure Patterns — Metadata Fingerprints

The hardest data incidents are **silent**: the pipeline reports success, nothing errors, but the
numbers are wrong. Root-causing them means recognizing the fingerprint each shape leaves in DataHub
metadata (custom properties, freshness, schema). Reason from these clues — never from a table named
"broken".

## 1. Silent partial load

- **Symptom:** a metric drops sharply overnight; no pipeline errors.
- **Fingerprint:** the raw source's `run_status` is `success`, but a `last_run_note` (or row-count
  history) shows far fewer rows than its recent average, and no backfill has run. Passthrough
  staging models and simple aggregates carry the shortfall silently downstream.
- **Confirm:** source API/incident log, row counts vs. the 7-day average, then trigger the backfill.

## 2. Schema drift (column rename/removal)

- **Symptom:** a field goes blank/null across a dashboard; no errors.
- **Fingerprint:** an upstream raw source changed its schema (e.g. `email` → `email_address`), but
  the downstream mapping was not updated, so the column now resolves to NULL. Schema tests that only
  check types pass anyway.
- **Confirm:** diff the source schema against the mapping; update the downstream model.

## 3. Stale / freshness failure

- **Symptom:** a metric looks "frozen" — unchanged for days.
- **Fingerprint:** the reference/feed table's last successful load is days old; the job "succeeds"
  but writes no new rows (upstream vendor feed down), so values are frozen while everything reports
  green.
- **Confirm:** last-load timestamp vs. expected cadence; check the upstream feed's status.

## Reasoning checklist

1. Does a clue's **magnitude and timing** match the reported symptom? (A 40% drop should line up
   with a ~40% row shortfall at about the right time.)
2. Is the clue at a **source/boundary** node (most causes) or a **passthrough** (usually just a
   carrier)?
3. If no clue matches at any hop, the honest answer is **insufficient evidence** — name the signal
   (an assertion, a run log, row-count history) that would resolve it.
