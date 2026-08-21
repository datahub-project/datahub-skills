---
name: using-datahub
description: |
  This skill provides routing guidance for all DataHub interaction skills. It is injected at session start and helps map user intent to the correct skill. Do not invoke this skill directly — it is loaded automatically.
---

# Using DataHub Skills

You have access to 6 DataHub catalog interaction skills. Use this guide to route the user's request to the correct skill.

---

## Skill Routing Table

| User Intent                                                                                       | Skill       | Command            |
| ------------------------------------------------------------------------------------------------- | ----------- | ------------------ |
| **Find or discover entities** (search, browse, filter, list)                                      | **Search**  | `/datahub-search`  |
| **Answer a question** about the catalog ("who owns X?", "how many X?")                            | **Search**  | `/datahub-search`  |
| **Update metadata** (descriptions, tags, glossary terms, ownership, deprecation)                  | **Enrich**  | `/datahub-enrich`  |
| **Explore lineage** (upstream, downstream, impact, root cause, dependencies)                      | **Lineage** | `/datahub-lineage` |
| **Data quality** (assertions, incidents, health checks)                                           | **Quality** | `/datahub-quality` |
| **Notifications** (subscribe to assertion failures, incidents)                                    | **Quality** | `/datahub-quality` |
| **Install CLI, authenticate, verify connection**                                                  | **Setup**   | `/datahub-setup`   |
| **Configure default scopes and profiles**                                                         | **Setup**   | `/datahub-setup`   |
| **Systematic scan for a systemic problem** (schema drift under a glossary term, coverage reports) | **Audit**   | `/datahub-audit`   |

---

## Disambiguation Rules

When the intent is ambiguous, use these rules:

### "Tag" requests

- **All tag operations** (PII, sensitive, important, reviewed, team-x) → **Enrich** (general metadata)

### "Domain" requests

- **Filter search to a domain** → **Search** (scoped search)
- **Configure default domain** → **Setup** (profile configuration)

### "Quality" or "health" requests

- **Failing assertions, active incidents, health status** → **Quality**
- **Create assertions, run quality checks, raise incidents** → **Quality**
- **Subscribe to assertion failures or incidents** → **Quality**
- **Metadata quality/documentation/ownership coverage** → Use **Search** to gather the data and synthesize the answer

### Lineage vs. Search

- **"What feeds into X" / "what depends on X" / "impact of changing X"** → **Lineage**
- **"What dashboards use table X"** → **Lineage** (relationship traversal)
- **"Who owns X" / "what is X"** → **Search** (metadata lookup)

### Setup vs. other skills

- **"Set up" / "install" / "authenticate" / "verify connection"** → **Setup**
- **"Configure defaults" / "set default platform" / "create profile"** → **Setup**
- **"Check if DataHub is working"** → **Setup** (connectivity verification)

### Audit vs. Search vs. Quality

- **One entity, one answer** ("who owns X?", "what columns does X have?") → **Search**
- **Systemic scan across many entities with a pattern-level verdict** ("check the Revenue term for schema drift", "how complete is our metadata") → **Audit**
- **Per-dataset assertions, incidents, health status** → **Quality**
- Audit currently only supports the Glossary Schema Consistency check — if the user asks for a different systematic report (metadata completeness, ownership coverage), tell them it isn't built yet and offer **Search** for a manual look instead of silently doing nothing.

---

## CLI Attribution

When running `datahub` CLI commands, pass `-C skill=<name>` on the root command so usage can be attributed:

```bash
datahub -C skill=datahub-search search "revenue"
datahub -C skill=datahub-enrich graphql --query '...'
datahub -C skill=datahub-lineage lineage --urn "..."
```

Use the skill name from the YAML frontmatter. If `-C` is not recognized, omit it — the command works the same without it.

---

## Critical Rules

1. **Never guess the skill.** If the intent is genuinely ambiguous, ask the user to clarify.
2. **One skill per request** unless the user explicitly asks for multiple operations.
3. **Lineage is for lineage only** — not for general "what is this entity?" questions (that's Search).
4. **Search handles ad-hoc questions.** "Who owns X?" and "what columns does X have?" are Search questions, not Lineage.
5. **Enrich handles all metadata writes** — descriptions, tags, glossary terms, ownership, deprecation.
6. **Quality handles data quality** — assertions, incidents, health checks, subscriptions.
7. **Setup handles environment and configuration** — CLI install, auth, connectivity, default scopes.
8. **Audit handles systemic scans, not single-entity questions** — a scan across many entities producing a pattern-level verdict (schema drift under a glossary term, coverage percentages). It's read-only and currently limited to Glossary Schema Consistency; say so if asked for anything broader.
