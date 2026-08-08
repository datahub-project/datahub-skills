---
name: catalog-document
description: Save answers as DataHub documents, or recall documents already written
argument-hint: "[what to save, or what to look up]"
---

# DataHub Document

Use the Skill tool to invoke the full `datahub-document` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-document"
```

**User's request:** $ARGUMENTS

This skill turns answers into durable catalog knowledge:

1. Search existing documents first, and cite one if it already answers the question
2. Decide whether a new answer is worth keeping
3. Write it question-first, naming every asset by URN, with a date
4. Save it with `save_document`
5. Verify the tool call happened before reporting success

If no arguments provided, ask whether to save something or look something up.
