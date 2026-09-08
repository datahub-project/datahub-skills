# Incident <!-- YYYY-MM-DD -->: <!-- symptom --> in <!-- asset name -->

**Asset**: <!-- full URN of the broken asset -->
**Detected**: <!-- timestamp from the report, or "unknown" -->
**Symptom**: <!-- nulls | freshness | schema | volume | failure | other --> — <!-- one factual sentence -->
**Status**: <!-- active | resolved -->

## Blast radius

<!-- N --> affected consumers within <!-- M --> hops. Score: <!-- total -->

Owners notified: <!-- deduplicated owner URNs, comma separated, or "none" -->

| Asset         | Type          | Hops       | Score        |
| ------------- | ------------- | ---------- | ------------ |
| <!-- name --> | <!-- type --> | <!-- n --> | <!-- x.x --> |

## Root cause hypotheses

1. <!-- statement --> — confidence <!-- N -->%
   - <!-- evidence line -->
   - Evidence URNs: <!-- urn, urn -->

## Resolution

<!-- What actually fixed it, filled in by the human. "Pending human confirmation." until then. -->

## Detection signals

<!-- What to watch for to catch this earlier next time: the field, the ancestor, the check that would have fired. -->

## Tags

<!-- Tags on THIS DOCUMENT, not on the assets: incident-triage, <symptom_type>, <cause_type>.
     The asset tags (incident-degraded, incident-impacted) are written in Step 6. -->

<!-- Everything below the title is retrieved by literal text match. Keep the asset URN, the symptom
type and the cause type verbatim, list every consumer row and every owner URN, and do not rename
the headings — a summarised or reworded postmortem is invisible to the next investigation. -->
