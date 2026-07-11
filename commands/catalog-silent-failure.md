---
name: catalog-silent-failure
description: Root-cause a silent failure — something degraded, but nothing errored
argument-hint: "[the asset that degraded, and when]"
---

# DataHub Silent Failure Root-Cause

Use the Skill tool to invoke the full `datahub-silent-failure` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-silent-failure"
```

**User's request:** $ARGUMENTS

Use this when a downstream consumer has degraded but **nothing errored** — a model
drifting, a dashboard going wrong, a metric moving with no failed job and no alert.

The skill:

1. Walks lineage upstream from the affected asset
2. Probes freshness at every hop **in the data plane** (ingestion metadata cannot
   see a stalled load — every table reports healthy)
3. Names the culprit: the first stale hop whose own upstream is fresh
4. Or exonerates the pipeline, if the data arrived on time and is simply unusual
5. Installs a freshness guard on the culprit, so the next occurrence is caught at
   the source

If the user reports a **hard** failure — a job errored, an alert fired, something
is red — that is not a silent failure. Use `datahub-quality` instead.

If no arguments provided, ask which asset degraded and on what date.
