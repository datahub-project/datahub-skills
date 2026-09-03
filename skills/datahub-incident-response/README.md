# datahub-incident-response

Evidence-backed diagnosis and reversible catalog containment for live data incidents.

## What It Does

- anchors a consumer-visible symptom to an exact DataHub entity;
- gathers bounded upstream lineage and metadata evidence;
- distinguishes hypotheses from confirmed production causes;
- identifies owners and the smallest confirming check;
- maps a complete, bounded downstream blast radius;
- proposes exact warning-tag writes and waits for approval;
- verifies every mutation and supports provenance-safe rollback.

It works in read-only mode when mutations are unavailable. Containment uses pre-existing DataHub tag
vocabulary; it does not repair pipelines or silently create governance metadata.

## Example Requests

```text
The revenue dashboard dropped 40% overnight. Find the likely fault location.
Customer emails became null after yesterday's load. What broke upstream?
Map the affected consumers and propose catalog containment, but do not write yet.
Roll back only the incident tags added by this response.
```

## Files

| File                                | Purpose                                                                  |
| ----------------------------------- | ------------------------------------------------------------------------ |
| `SKILL.md`                          | Investigation, approval, containment, verification, and closure workflow |
| `references/incident-patterns.md`   | Hypothesis patterns with weakening evidence and confirming checks        |
| `references/containment-runbook.md` | Mutation, partial-failure, and rollback checklist                        |
| `evaluations/*.json`                | Forward-test scenarios for critical behavior                             |
