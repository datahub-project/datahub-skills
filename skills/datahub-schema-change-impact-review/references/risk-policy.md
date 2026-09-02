# Deterministic Risk Policy

This policy is authoritative. An agent or LLM may explain it but must not add,
remove, or change points.

## Operation Base Weight

| Change        | Points |
| ------------- | -----: |
| Add column    |      2 |
| Rename column |     12 |
| Change type   |     18 |
| Drop column   |     25 |

## Blast Radius

Apply at most one blast-radius factor:

| Unique downstream assets | Factor                              | Points |
| -----------------------: | ----------------------------------- | -----: |
|                      0–1 | None                                |      0 |
|                      2–4 | Multiple downstream dependencies    |      6 |
|                      5–9 | Significant downstream blast radius |     12 |
|                      10+ | Large downstream blast radius       |     20 |

## Evidence Factors

- Downstream dashboards/charts: 15 points for the first and 5 for each
  additional asset, capped at 25.
- Production ML dependency: 25 points when any ML model or feature table is
  affected.
- Business-critical assets: `8 + 4 × count`, capped at 20, when affected assets
  have high or critical explicit DataHub criticality or the clearly labeled
  deterministic fallback.
- Governed root: 10 points when the root has a real `PII`, `SENSITIVE`, `SOX`,
  `HIPAA`, or `GDPR` tag.
- Existing quality failure: 10 points when an identifiable DataHub quality or
  assertion result is failing.
- High usage: 10 points only when a defensible DataHub usage score is at least 70. Do not invent a normalized score.
- Cross-team coordination: 2 points per distinct real owner label across
  affected assets, capped at 10.

Every applied factor must include supporting evidence. Do not fabricate owners,
tags, quality, usage, or lineage to activate a factor. Criticality evidence must
state whether it is explicit DataHub metadata or inferred fallback.

## Score and Decision

Raw score is the sum of factor points. Final score is `min(100, raw score)`.

| Final score | Risk     | Decision |
| ----------: | -------- | -------- |
|        0–24 | LOW      | ALLOW    |
|       25–49 | MEDIUM   | REVIEW   |
|       50–74 | HIGH     | BLOCK    |
|      75–100 | CRITICAL | BLOCK    |

Generated narrative, safeguards, optional model output, and mutation status do
not change the score or decision.
