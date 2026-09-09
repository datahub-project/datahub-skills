---
name: catalog-onboarding
description: Onboard a new data-team member, capture a departing member's knowledge as a runbook, or validate an existing onboarding doc against the live DataHub catalog
argument-hint: "[role + domain to onboard | task to capture | document to validate]"
---

Use the Skill tool to invoke the full `datahub-onboarding` skill:

```
Skill tool:
  skill: datahub-skills:datahub-onboarding
```

**User's request:** $ARGUMENTS

If no arguments are provided, ask which of three jobs the user wants. Orienting a new
team member, in which case ask for their role and domain. Capturing a departing member's
task knowledge as a runbook, in which case ask for the task. Or validating an existing
runbook or onboarding document against the live catalog.
