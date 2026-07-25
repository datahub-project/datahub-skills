# Impact Gate: {{VERDICT}}

<!-- VERDICT is one of PASS / REVIEW / BLOCK -->

**Change:** {{change summary — e.g. drop column `airport_fee` (DOUBLE)}} on `{{dataset name}}` (`{{env}}`)
**Dataset URN:** `{{dataset urn}}`
**Classification:** {{breaking | non-breaking | unknown→breaking}} ({{change kind}})
**Lineage read:** skip-cache `searchAcrossLineage` DOWNSTREAM · {{N}} entities · fresh: {{yes/no}}

---

## Downstream blast radius

<!-- List impacted ML models and dashboards. If none, say "No downstream ML models or dashboards found." -->

| Hop | Entity        | Type      | Owner(s)    | Note                          |
| --- | ------------- | --------- | ----------- | ----------------------------- |
| 1   | {{feature}}   | mlFeature | {{owner/—}} | sources: this dataset         |
| 2   | {{model}}     | mlModel   | {{owner/—}} | consumes the impacted feature |
| 1   | {{dashboard}} | dashboard | {{owner/—}} | reads this dataset            |

## Why {{VERDICT}}

{{One or two sentences tying the change classification to the impacted consumers and the rubric.
For BLOCK: name the production consumer at risk.
For REVIEW: state what needs human sign-off (additive change with downstream surface / unowned / partial lineage).
For PASS: state that nothing downstream can break.}}

## Caveats

<!-- Include only if relevant. Delete the section on a clean PASS. -->

- {{e.g. lineage may be incomplete or not yet ingested — a breaking change with an empty downstream set is REVIEW, not PASS}}
- {{e.g. impacted model `X` has no owner}}

## Recommended next steps

- {{Notify the listed owner(s) before proceeding.}}
- {{If the change is intended, migrate the downstream consumer first, then re-run the gate.}}
- {{To record the risk in DataHub (incident / assertion / ownership), use `/datahub-quality`.}}
