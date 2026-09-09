# Resolving which value is authoritative

Everything else in this workflow depends on getting this right. If the
authoritative source is misidentified, the corrections are inverted: the stale
value gets pushed into the correct system, and the resulting damage is wider
than the original drift.

---

## Look for an explicit marker

Organisations record this differently. Check, in roughly this order:

1. **Structured property** — e.g. `<org>.authority = authoritative`, or
   `system_of_record = true`. The most reliable signal when present, because it
   is deliberate and typed.
2. **Tag** — `source-of-truth`, `golden`, `authoritative`, `system-of-record`.
3. **Domain** — membership of a domain such as "Systems of Record" or
   "Master Data".
4. **Glossary term** — a term like `AuthoritativePrice` attached to the asset or
   to a specific column.
5. **Data product** — some catalogs designate one output port per product as
   canonical.

Column-level markers beat asset-level ones. An asset can be authoritative for
price and merely a projection for inventory.

---

## Signals that are *not* authority

Do not resolve authority from any of these, alone or combined:

- **Recency.** A stale downstream system can be written to more recently than
  the source.
- **Platform.** A warehouse table is not authoritative because it is in the
  warehouse; commerce truth usually lives in the commerce platform.
- **Search rank.** Ordering reflects relevance, not governance.
- **Being upstream in lineage.** Lineage tells you what derives from what, which
  is usually but not always the same as what is correct. A backfill can invert
  it.
- **Row count or freshness metrics.** Volume is not correctness.

---

## When nothing is marked

Stop and say so. This is a legitimate, useful outcome: "the catalog does not
record which of these three prices is authoritative" is exactly the finding the
organisation needs, and it is the prerequisite for every future automated check.

Report:

- the candidate assets you found and their lineage relationship
- the differing values
- what marker is missing, and where it would go

Then propose adding the marker as a governance change for a human to approve.
Do not proceed to corrections on an assumed source.

---

## When two assets are both marked

Treat conflicting markers as a governance defect, not a tiebreak to resolve.
Report both, and do not guess. Two systems of record for the same field is the
root cause of the drift you were asked to assess.

---

## Sanity-check the authoritative value itself

Before propagating anything, check the source value is plausible:

- negative or absent inventory
- a price of zero, or a price orders of magnitude from the previous value
- a policy window of zero days
- a status that contradicts the change (discontinued but repriced)

A bad source produces confidently wrong corrections in every downstream system
at once. It is worth one comparison against the previous value to catch a
fat-fingered edit or a failed upstream job before amplifying it.
