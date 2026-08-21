# Template: proposing a leakage-signal glossary term

When an audit finds a credible target-leakage risk and no existing glossary
term captures "this data reflects the outcome, not a predictor of it,"
propose one instead of a one-off tag. A shared, well-defined term compounds:
every future audit (by an agent or a human) can reuse the same signal
instead of re-deriving it from column names.

## Definition to propose

- **Name:** `PostOutcomeEvent`
- **Definition:** "Data whose events are only recorded after the business
  outcome (e.g. a churn, a default, a fraud confirmation) has already
  occurred. Features derived from these sources risk leaking the label into
  training data."
- **Term source:** `INTERNAL`
- **Where to attach it:** any raw or staging dataset whose population is
  causally downstream of the outcome you're trying to predict -- refund
  logs, cancellation reasons, support-ticket resolutions, chargebacks,
  churn-survey responses, etc.

## How to create it (MCP)

Glossary terms must exist before they can be attached. If you have
mutation access and a `create_glossary_term`-style tool is available, use
it; otherwise create it via ingestion (the `acryl-datahub` Python SDK's
`GlossaryTermInfoClass` aspect, emitted via `MetadataChangeProposalWrapper`,
is the standard way) or the DataHub UI, then attach with
`add_terms(entity_urns=[...], term_urns=["urn:li:glossaryTerm:PostOutcomeEvent"])`.

## Detector pattern once the term exists

```python
upstream = get_lineage(urn=model_urn, upstream=True, max_hops=6)
tainted = [
    e for e in upstream["upstreams"]["searchResults"]
    if e["entity"]["type"] == "DATASET"
    and any(
        t["term"]["urn"] == "urn:li:glossaryTerm:PostOutcomeEvent"
        for t in (e["entity"].get("glossaryTerms") or {}).get("terms", [])
    )
]
```

If `tainted` is non-empty, you have a provable leakage finding grounded in
governance metadata, not a guess from column names.
