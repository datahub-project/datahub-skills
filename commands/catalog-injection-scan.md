---
name: catalog-injection-scan
description: Sweep the DataHub catalog for prompt-injection payloads and remediate them with approval
argument-hint: "[what to scan, or what to do with the findings]"
---

# Antigen Scan

Use the Skill tool to invoke the full `antigen-scan` skill:

```
Skill tool:
  skill: "datahub-skills:antigen-scan"
```

**User's request:** $ARGUMENTS

This skill finds and removes prompt-injection payloads (OWASP LLM01) planted in catalog free-text:

1. Sweep entity descriptions, column descriptions, and KB documents read-only
2. Score every surface with a deterministic standard-library rule — no model call
3. Print the exact mutation plan (URN, tool, field, before → after) and write nothing
4. Get explicit human approval
5. Remove the injected span, quarantine-tag, stamp tamper-evidence hashes, file a hash-only forensic incident
6. Map two-hop downstream reach, certify the clean remainder, re-scan to prove the control is standing

Every mutating command is dry-run by default against a live catalog; `--apply` is required to write. A degraded sweep exits 2 and is never an all-clear.

Requires an [Antigen](https://github.com/edycutjong/antigen) checkout. If no arguments are provided, run the read-only sweep and report.
