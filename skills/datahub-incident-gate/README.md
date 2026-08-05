# DataHub Incident Gate

Fail-closed incident response for DataHub agents: trust fitness + blast radius before any metadata write, then HITL and mutation-disabled verify.

## What it does

1. Normalizes a monitoring / incident signal
2. Scores live catalog fitness (owners, assertions, lineage, freshness, docs)
3. **Blocks write offers** when trust fails (hard gate on assertion failure)
4. Ranks downstream blast via lineage
5. Requires scoped human approval before mutations
6. Verifies writes from a fresh mutation-disabled session

## Usage

```
/datahub-incident-gate assertion failed on fct_users_created — can we tag it?
/datahub-incident-gate fail-closed review for this dataset before write
/datahub-incident-gate verify the incident document with mutations disabled
```

## Install

```bash
npx skills add datahub-project/datahub-skills --skill datahub-incident-gate
```

## Provenance

Generalized from [SignalTower](https://github.com/HiAbhishekh/signaltower) (Apache-2.0).
