---
name: catalog-agent-forensics
description: Investigate AI-agent decision evidence, impact, approvals, and replay safety
argument-hint: "[receipt, decision, field, incident, or forensic question]"
---

# DataHub Agent Forensics

Use the Skill tool to invoke the full `datahub-agent-forensics` skill:

```text
Skill tool:
  skill: "datahub-skills:datahub-agent-forensics"
```

**User's request:** $ARGUMENTS

This skill investigates agent decisions through DataHub:

1. Resolve the exact receipt, run, incident, field, or campaign
2. Directly retrieve governed DataHub evidence
3. Verify the signed artifact when available
4. Separate recorded influence from generic lineage
5. Apply deterministic impact and replay-safety policy
6. Produce a raw-free forensic report with explicit limitations
7. Preserve unavailable receipt or incident evidence, configured-index scope, and
   read-only authority

If no arguments are provided, ask which agent decision, receipt, incident, or field
to investigate.
