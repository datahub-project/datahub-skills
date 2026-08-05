---
description: Fail-closed incident gate — trust + blast before DataHub writes, then HITL and mutation-disabled verify
---

Use the `datahub-incident-gate` skill.

Normalize the incident signal, score live trust fitness, rank blast radius, and **do not offer writes on BLOCK**. On ALLOW, present a scoped plan, wait for explicit approve/reject, execute only approved actions, then verify from a fresh mutation-disabled session.
