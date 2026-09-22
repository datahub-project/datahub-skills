# Compliance Impact Analysis (Data Subject Request)

## Request

**Subject ID:** <!-- id or reference for the person the request concerns -->
**Request type:** <!-- deletion / access / correction -->
**Source column:** <!-- PII-tagged column the request originates from, e.g. customers.email -->

## Traversal

**Direct dependents (1 hop):** <!-- count -->
**Transitive dependents (all hops):** <!-- count -->
**Depth traced:** <!-- hops -->

## Findings

Unlike a structural impact analysis, each downstream entity here needs a
judgment call, not just a count: does it still expose the individual's raw
data, or is it aggregated enough that they're no longer identifiable? Don't
skip straight to "no action" without a reason — an empty description is a
reason to mark **Needs review**, not a reason to assume it's safe.

### Action needed (raw exposure)

| Entity        | Type          | Platform          | Why                                                    |
| ------------- | ------------- | ----------------- | ------------------------------------------------------ |
| <!-- name --> | <!-- type --> | <!-- platform --> | <!-- row-level grain, direct filter on the subject --> |

### Needs review (insufficient information)

| Entity        | Type          | Platform          | Why unclear                                    |
| ------------- | ------------- | ----------------- | ---------------------------------------------- |
| <!-- name --> | <!-- type --> | <!-- platform --> | <!-- no description, ambiguous aggregation --> |

### No action (aggregated / not identifiable)

| Entity        | Type          | Platform          | Why safe                                             |
| ------------- | ------------- | ----------------- | ---------------------------------------------------- |
| <!-- name --> | <!-- type --> | <!-- platform --> | <!-- aggregation level, grain, no per-row output --> |

## Write-back (if the deployment tier supports it)

<!-- Which tags/notes were applied to which entities, and why write-back
     over just reporting -- the next reviewer or agent should inherit this
     finding instead of re-deriving it from scratch. -->

## Recommendations

1. <!-- Who to notify for "action needed" entities (use ownership from lineage results) -->
2. <!-- What to escalate for "needs review" entities -->
