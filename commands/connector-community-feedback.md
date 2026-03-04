---
name: connector-community-feedback
description: Guide a community member through field-testing a DataHub connector and collecting structured feedback
argument-hint: "[PR URL, PR number, or connector name]"
---

# DataHub Connector Community Feedback

Use the Skill tool to invoke the `datahub-connector-community-feedback` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-connector-community-feedback"
```

**User's request:** $ARGUMENTS

The skill guides the tester through 7 phases:

1. **Discovery** — fetch PR details or identify the connector version being tested
2. **Tester profile** — understand their source system, deployment, and DataHub environment
3. **Testing mode + scenario scoping** — choose Quickstart / production / no-instance, then narrow down which assets and features to test
4. **Pre-flight + install + config** — environment checks, install the connector, generate a credential-safe recipe using `${ENV_VAR}` references
5. **Verification** — pre-generated pass/fail checklist of scenarios to validate in the DataHub UI
6. **Structured feedback** — conversational Q&A on setup, coverage, features, and edge cases
7. **Output** — preview the full report, then optionally post as a PR comment, GitHub Issue, and/or save locally

If no arguments provided, ask what the tester wants to test.
