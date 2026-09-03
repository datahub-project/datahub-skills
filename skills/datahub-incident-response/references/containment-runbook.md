# Catalog Containment Runbook

This runbook covers reversible warning tags. It does not stop pipelines, repair records, or create a
native DataHub incident.

## Preflight

- [ ] User asked for or is considering containment.
- [ ] Leading fault location is an exact fetched URN.
- [ ] Downstream set is fully enumerated, deduplicated, and within the agreed hop boundary.
- [ ] Pagination or truncation metadata proves the set used for writing is complete.
- [ ] Every target was fetched and its current tags were recorded.
- [ ] Warning tag entities already exist.
- [ ] `add_tags` and `remove_tags` are available and authorized.
- [ ] The plan lists exact tag/entity pairs, counts, exclusions, effect, and rollback.
- [ ] The user explicitly approved that exact plan.

## Apply and Verify

Track each tag/entity pair independently:

| Tag URN | Entity URN | Pre-state      | Mutation result | Readback             | Final state    |
| ------- | ---------- | -------------- | --------------- | -------------------- | -------------- |
| `<tag>` | `<entity>` | absent/present | success/failure | present/absent/error | classification |

Valid final classifications are:

- `verified added`: absent before, mutation attempted, present on readback;
- `unchanged/pre-existing`: present before and still present;
- `failed`: mutation returned failure and readback does not show the tag;
- `unverified`: readback was unavailable or contradictory.

Do not count pre-existing pairs as work performed, but re-fetch them with the rest of the approved
plan so the final state is explicit. Stop subsequent batches after a failure or an unverified
result.

## Partial Failure

Report five disjoint sets:

1. verified additions;
2. unchanged/pre-existing pairs;
3. failed pairs;
4. unverified pairs;
5. unattempted pairs.

State `partially contained`, not `contained`. Offer either a bounded retry after the cause is known
or rollback of the verified additions. Exclude an unverified pair from rollback until readback
establishes whether it persisted and whether this run added it.

## Rollback

Rollback operates only on pairs classified `verified added` in this run:

1. show the exact removal plan and obtain approval, unless automatic rollback on failure was part of
   the original approval;
2. call `remove_tags` for only those pairs;
3. re-fetch every entity;
4. classify each pair as confirmed absent, still present, or unverified;
5. claim `rolled back` only when every run-owned pair is confirmed absent.

Never remove a tag that was present in the pre-state, even if the current incident no longer needs
it. Its provenance belongs to another actor or process.
