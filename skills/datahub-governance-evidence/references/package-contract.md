# Evidence package contract

Use this contract when rendering Markdown and JSON from one collection run.

## Required invariants

1. Use one immutable selected-asset boundary for all signals.
2. Include each selected URN exactly once in `assets`.
3. Include exactly one state per selected asset and collected signal.
4. Use only `Observed`, `Not observed`, and `Unable to determine`.
5. For every signal, require:
   - `observed + not_observed + unable = selected_assets`
   - the three URN sets are disjoint
   - their union equals the selected boundary
   - counts equal URN-set lengths
   - percentages equal count divided by selected assets, rounded consistently
6. Keep complete URN sets in JSON. Do not replace them with top-N samples.
7. Derive framework breakdowns from observation states; never recollect or
   reinterpret an asset state for a framework.
8. Require every symbolic Structured Property signal to bind to one exact
   qualified name in the collection record.
9. Keep collection errors safe: operation, asset URN, error class/summary, and
   completeness effect; never include credentials or response bodies.
10. Require the fixed disclaimer in both formats.
11. Embed safe collection-operation shapes and the exact page/cursor sequence
    in JSON; do not require a separate local command log to understand scope.
12. Escape untrusted catalog text before placing it in Markdown or HTML.

## Markdown/JSON reconciliation

Compare before delivery:

- collection timestamp, server/version, scope filters, and completeness
- selected asset count and exact URN boundary
- summary counts and percentages
- named not-observed and unable populations
- framework identifiers, per-signal populations, relevance, and limitations
- collection errors and follow-up candidates

Markdown must include exact URNs for named gaps and framework populations. It
may shorten asset rows only when it says so and points to the complete JSON.
JSON must remain complete.

## Structured format

Copy `templates/governance-evidence-package.template.json` and replace every
placeholder. Preserve its field names and types. Add one `summary` object for
each collected signal and one `observations` object per asset/signal pair.

Each framework entry includes review focus, relevant signals, source surfaces,
per-signal counts and exact populations, evidence relevance, limitation, and an
authoritative-source link. Do not add `score`, `grade`, `pass`, `fail`,
`readiness`, `compliant`, or `control_status` fields. A framework entry is an
evidence alignment only.

## File integrity

When a checksum tool is available:

```bash
shasum -a 256 governance-evidence.md governance-evidence.json
```

Record the hashes beside the files. A checksum detects file changes; it does
not validate source truth, completeness, compliance, or legal sufficiency.
