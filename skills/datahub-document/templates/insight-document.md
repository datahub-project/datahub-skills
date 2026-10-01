# Template: insight document

Use this shape when saving an answer to DataHub. Keep it under roughly a screen and a half —
the value is in being findable and checkable, not exhaustive.

---

## Title

State the question the way someone would search for it.

- Good: `Which dashboards break if snowflake orders_raw fails`
- Good: `Why customer_email is deprecated in the analytics domain`
- Weak: `Orders analysis`, `Notes`, `Investigation 2026-08`

## Body

```markdown
**Question**

<the question as asked, in plain language>

**Answer**

<the answer, leading with the conclusion>

**Assets involved**

- `<name>` — `<urn>` — <role: source, intermediate, consumer>
- `<name>` — `<urn>` — <role>

**How this was derived**

<which tools and hops produced the answer — e.g. "downstream lineage from
urn:li:dataset:(...orders_raw...), 2 hops, filtered to dashboards">

**Caveats**

<what this does not cover: unmapped lineage, platforms outside the catalog,
assumptions made>

_Derived <YYYY-MM-DD>. Re-check if lineage or ownership has changed since._
```

## Owners and routing

If the answer concerns assets with owners, name them so the document reaches the right team.
Where the catalog exposes domains, mention the domain — it is how most readers browse.

## When to update instead of create

If recall mode found a document covering the same question, update that one and note what
changed. Two documents with divergent answers are worse than one stale document.
