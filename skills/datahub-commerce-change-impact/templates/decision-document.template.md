# Commerce change resolution: {{ SKU_OR_ENTITY }}

<!--
Write this back to the catalog after a human has approved and any correction has
been validated. Attach it to the affected assets so the next reader inherits it.
Keep it readable by someone who was not involved.
-->

## What changed

- **Authoritative source:** `{{ SOURCE_URN }}`
- **Field(s):** {{ FIELDS }}
- **New value(s):** {{ VALUES }}
- **Observed at:** {{ TIMESTAMP }}

## What was wrong

<!-- One bullet per contradiction. Expected vs observed, and the customer-visible
     consequence in plain language. -->

- **{{ FINDING_TITLE }}** ({{ SEVERITY }}) on `{{ DOWNSTREAM_URN }}`
  - expected `{{ EXPECTED }}`, observed `{{ OBSERVED }}`
  - {{ CUSTOMER_IMPACT }}
  - owner: {{ OWNER_OR_NONE }}

## Blast radius

<!-- How the affected assets were discovered — the lineage path, not a list
     someone typed. State the hop count used. -->

Resolved from {{ EDGE_COUNT }} lineage edges downstream of the source
(max {{ HOPS }} hops).

| Asset | Channel | Criticality | Owner |
| --- | --- | --- | --- |
| `{{ ASSET }}` | {{ CHANNEL }} | {{ CRITICALITY }} | {{ OWNER }} |

## How it was resolved

- **Corrections applied:** {{ WHAT_CHANGED_WHERE }}
- **Validation:** {{ VALIDATION_RESULT }}
- **Change record:** {{ PR_OR_TICKET_URL }}
- **Approved by:** {{ APPROVER }} at {{ APPROVED_AT }}

<!-- If anything was deliberately not fixed, say so and why. A known, accepted
     divergence is useful; a silently skipped one is not. -->

**Not corrected:** {{ WHAT_WAS_LEFT_AND_WHY }}

## For whoever comes next

<!-- The part that pays for the document. What should someone know before they
     touch this again? -->

These surfaces project from `{{ SOURCE_URN }}`. If {{ FIELDS }} changes at the
source, expect each asset above to need re-deriving — {{ WHICH_ONES_ARE_PINNED }}
hold pinned values that will not follow automatically.

{{ ANY_STRUCTURAL_FIX_WORTH_MAKING }}
