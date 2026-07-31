---
name: catalog-learnings
description: Recall prior agents' learnings about a dataset before working with it, and retain new ones after
argument-hint: "[dataset name or urn, or a finding to retain]"
---

# DataHub Learnings

Use the Skill tool to invoke the full `datahub-learnings` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-learnings"
```

**User's request:** $ARGUMENTS

This skill runs the agent-memory protocol against DataHub in two workflows:

1. **Recall:** Before touching a dataset, read prior agents' learnings (semantic gotchas, verified queries, join traps, caveats, metric definitions) for that dataset and its direct upstream lineage
2. **Retain:** After finishing a task, distill what was learned and write it back to the dataset's DataHub page as structured properties plus a rendered documentation block

If no arguments provided, ask which dataset the user is about to work with, or what finding they want to retain.
