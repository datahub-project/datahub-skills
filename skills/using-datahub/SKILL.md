---
name: using-datahub
description: |
  This skill provides routing guidance for all DataHub interaction skills. It is injected at session start and helps map user intent to the correct skill. Do not invoke this skill directly — it is loaded automatically.
---

# Using DataHub Skills

Use this guide to route the user's request to the correct DataHub catalog interaction skill.

---

## Skill Routing Table

| User Intent                                                                      | Skill                    | Command                                |
| -------------------------------------------------------------------------------- | ------------------------ | -------------------------------------- |
| **Find or discover entities** (search, browse, filter, list)                     | **Search**               | `/datahub-search`                      |
| **Answer a question** about the catalog ("who owns X?", "how many X?")           | **Search**               | `/datahub-search`                      |
| **Update metadata** (descriptions, tags, glossary terms, ownership, deprecation) | **Enrich**               | `/datahub-enrich`                      |
| **Explore lineage** (upstream, downstream, impact, root cause, dependencies)     | **Lineage**              | `/datahub-lineage`                     |
| **Certify a risky dataset field change** (safe package, approval hash, passport) | **Schema certification** | `/datahub-schema-change-certification` |
| **Data quality** (assertions, incidents, health checks)                          | **Quality**              | `/datahub-quality`                     |
| **Notifications** (subscribe to assertion failures, incidents)                   | **Quality**              | `/datahub-quality`                     |
| **Install CLI, authenticate, verify connection**                                 | **Setup**                | `/datahub-setup`                       |
| **Configure default scopes and profiles**                                        | **Setup**                | `/datahub-setup`                       |

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

### Lineage vs. Schema Certification

- **"What breaks if I change X?" / exploratory impact analysis** → **Lineage**
- **"Certify this rename/drop/type change" / safe delivery package / scope-bound approval / change passport** → **Schema Certification**
- Schema Certification requires the official DataHub MCP server. A CLI-only or unavailable MCP session remains `NOT_RUN`; do not simulate live evidence.

### Setup vs. other skills

- **"Set up" / "install" / "authenticate" / "verify connection"** → **Setup**
- **"Configure defaults" / "set default platform" / "create profile"** → **Setup**
- **"Check if DataHub is working"** → **Setup** (connectivity verification)

---

## CLI Attribution

When running `datahub` CLI commands, pass `-C skill=<name>` on the root command so usage can be attributed:

```bash
datahub -C skill=datahub-search search "revenue"
datahub -C skill=datahub-enrich graphql --query '...'
datahub -C skill=datahub-lineage lineage --urn "..."
```

Schema Certification uses host-exposed DataHub MCP tools rather than a DataHub CLI fallback. The bundled Python helper computes policy decisions locally but never calls DataHub.

Use the skill name from the YAML frontmatter. If `-C` is not recognized, omit it — the command works the same without it.

---

## Critical Rules

1. **Never guess the skill.** If the intent is genuinely ambiguous, ask the user to clarify.
2. **One skill per request** unless the user explicitly asks for multiple operations.
3. **Lineage is for lineage only** — not for general "what is this entity?" questions (that's Search).
4. **Search handles ad-hoc questions.** "Who owns X?" and "what columns does X have?" are Search questions, not Lineage.
5. **Enrich handles ordinary metadata writes** — descriptions, tags, glossary terms, ownership, deprecation. Scope-bound schema-change decision write-back belongs to Schema Certification.
6. **Quality handles data quality** — assertions, incidents, health checks, subscriptions.
7. **Setup handles environment and configuration** — CLI install, auth, connectivity, default scopes.
8. **Schema Certification is a closed decision protocol** — use it only for an explicit risky field-change certification request; deterministic evidence is authoritative, and no write-back may run without approval bound to the exact scope hash.
