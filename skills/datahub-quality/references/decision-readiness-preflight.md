# Proposed DataHub Skills contribution

## Target repository

`datahub-project/datahub-skills`

## Proposed path

`skills/datahub-quality/references/decision-readiness-preflight.md`

## Purpose

Give agents a safe, read-only way to decide whether a dataset has enough current
metadata for a requested AI action. This is a quality workflow, not a new
quality score. It makes the evidence behind a decision explicit and avoids
treating an API limitation as proof that metadata is absent.

## Proposed file

### Decision-readiness preflight

Use this preflight before an agent explains, summarizes, modifies, or acts on a
dataset. The preflight is read-only unless the user separately approves a
mutation.

#### 1. Identify the asset

- Resolve the dataset URN and platform.
- Record the DataHub deployment and evaluation timestamp.
- Keep one graph scope for every query in the assessment.

#### 2. Classify each evidence signal

For every required signal, return exactly one of these states:

- **Present**: the signal exists and its latest fact is inside the active policy window.
- **Absent**: the deployment answered successfully, but no qualifying fact exists.
- **Unavailable**: the deployment could not answer the field, the field is not
  supported by this version, or the request failed. Unavailable is not the same
  as absent.
- **Stale**: a fact exists, but its timestamp is outside the policy window.

Never silently convert `Unavailable` into `Absent`.

#### 3. Inspect the latest quality facts

For each assertion attached to the dataset, show:

- assertion name and type;
- latest run timestamp;
- latest result (`PASS`, `FAIL`, or unknown);
- evaluation timestamp and policy freshness window.

Only the latest run for each assertion should determine the current result. A
dataset does not pass the assertion check merely because an older run passed.

Also inspect freshness and incidents:

- freshness timestamp and the expected SLA;
- open incident status and the incident's latest update timestamp;
- whether the latest fact is available under the current deployment's schema.

#### 4. Inspect context coverage

Report the underlying facts rather than only a score:

- named owners;
- approved glossary terms;
- upstream and downstream lineage counts;
- column count and column-lineage coverage, when both are available;
- usage or query activity timestamp, when available;
- policy or access-control evidence relevant to the requested action.

If column lineage is unavailable, report coverage as `unavailable`; do not report
zero covered columns.

#### 5. Apply the action-specific gate

Use stricter requirements for higher-impact actions:

- **Explain**: description and basic ownership/context may be enough.
- **Summarize or generate metrics**: require definitions, freshness, quality
  evidence, and enough lineage to explain the result.
- **Modify or take autonomous action**: require current ownership, approved
  definitions, complete relevant lineage, current passing assertions, no open
  incidents, freshness inside policy, and a permission check.

An unavailable required signal should block the action or require human review.
The response should name the exact signal and why it could not be verified.

#### 6. Return an evidence-backed decision

Return a compact decision with:

```json
{
  "decision": "allowed | caution | blocked",
  "asset": "<dataset urn>",
  "evaluated_at": "<timestamp>",
  "action": "<requested action>",
  "evidence": {
    "assertions": "present | absent | unavailable | stale",
    "freshness": "present | absent | unavailable | stale",
    "incidents": "clear | open | unavailable",
    "lineage": "complete | partial | unavailable",
    "ownership": "present | absent | unavailable"
  },
  "blocking_reasons": [
    "Latest assertion `daily_row_count` failed at <timestamp>"
  ],
  "next_step": "<specific steward action>"
}
```

Do not claim that an action is safe from a score alone. A score is a summary;
the decision must remain traceable to the current DataHub evidence.

#### Example requests

- “Is this dataset ready for an agent to explain?”
- “Before generating executive metrics, show the latest assertion result,
  freshness timestamp, open incidents, and lineage coverage.”
- “Can the agent modify this dataset? Block it if any required fact is stale or
  unavailable, and tell me exactly what a steward must repair.”

## Why this belongs in DataHub Skills

The quality skill already covers assertions and incidents. This reference adds
the missing decision layer for agents: current evidence, deployment-aware
unknowns, action-specific safeguards, and a reproducible response shape.
