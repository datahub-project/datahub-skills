---
name: datahub-document
description: |
  Use this skill when the user wants to capture knowledge into DataHub or read what has already been captured — saving an answer, decision, runbook, incident write-up or FAQ as a DataHub document, or searching existing documents before answering a question. Triggers on: "save this to DataHub", "write this up in the catalog", "document this decision", "is there a runbook for X", "what do our docs say about X", "search our knowledge base". For metadata on an entity (descriptions, tags, glossary terms, ownership), use `/datahub-enrich`. For finding entities themselves, use `/datahub-search`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Documents

You help the user turn answers into durable catalog knowledge, and reuse knowledge that
already exists instead of re-deriving it.

A data team answers the same questions repeatedly — _what feeds this table, why is this
column deprecated, what do we do when this pipeline fails_ — and the answers usually live in
someone's memory or a Slack thread. DataHub documents are where that knowledge belongs,
next to the assets it describes.

This skill operates in two modes:

- **Recall mode:** search existing documents before answering, so prior work is reused
- **Capture mode:** save a new answer, decision or runbook as a document

---

## Multi-Agent Compatibility

This skill works across coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI,
Windsurf, and others).

**What works everywhere:** both modes, document search and retrieval, and saving via MCP
tools or the DataHub CLI.

**Claude Code-specific:** `allowed-tools` in the frontmatter above. Other agents can ignore it.

**Reference file paths:** shared references are in `../shared-references/`; this skill's own
references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to...                                         | Use this instead   |
| --------------------------------------------------------------- | ------------------ |
| Set a description, tag, glossary term or owner **on an entity** | `/datahub-enrich`  |
| Find datasets, dashboards or other entities                     | `/datahub-search`  |
| Trace upstream or downstream lineage                            | `/datahub-lineage` |
| Create assertions, investigate incidents                        | `/datahub-quality` |

**Key boundary:** Enrich writes metadata that is _attached to an entity_. Document writes
_standalone knowledge_ — a page that can reference many entities and outlives any one of
them. "Describe this column" is Enrich. "Write up why this pipeline broke" is Document.

---

## Recall Mode: check before you answer

Before answering a substantive question about the data estate, look for an existing document.

1. **Search by keyword** — `search_documents(query, filter=...)`, filtering on platform,
   domain, tag, glossary term or owner.
2. **Search inside content** — `grep_documents(urns, pattern)` narrows to specific phrasing
   ("retention policy", `PII.*review`). It takes the **URNs to search within**, so it is a
   second step rather than an alternative first one: collect URNs from `search_documents`,
   then grep inside them. Calling it without `urns` fails.
3. **Cite what you find.** If a document already answers the question, lead with it and link
   it. Say when it was last updated, and flag it if it looks stale.

If document tools are unavailable, the catalog has no documents yet — go straight to capture
mode. `search_documents` and `grep_documents` are hidden when no documents exist, so their
absence is information, not an error.

---

## Capture Mode: save the answer

### Step 1 — Decide whether it is worth saving

Save when the answer took real work to derive, or when the next person would otherwise
repeat it: impact analyses, incident post-mortems, "why is it like this" explanations,
onboarding notes, metric definitions.

Do not save trivia ("this table has 12 columns"), anything already captured in an entity
description, or unverified speculation.

### Step 2 — Write it for the next reader

Use the structure in `templates/insight-document.md`. The essentials:

- **A title that matches how someone will search for it.** "Which dashboards break if
  `orders` fails" beats "Orders analysis".
- **The question first, then the answer.** People arrive with a question.
- **Every asset named with its URN.** A document that says "the orders table" is ambiguous
  across platforms; one with `urn:li:dataset:(urn:li:dataPlatform:snowflake,...)` is not.
- **How it was derived.** Which lineage hops, which queries. This is what makes the document
  checkable later rather than folklore.
- **A date.** Metadata moves; a reader needs to judge staleness.

### Step 3 — Save it

Call `save_document(document_type, title, content)`. All three are required — `document_type`
is easy to forget, and the call fails without it. Pick the one that fits:

`Insight` · `Decision` · `FAQ` · `Analysis` · `Summary` · `Recommendation` · `Note` · `Context`

An impact analysis is `Analysis`, a post-mortem conclusion is `Insight`, "why we chose X" is
`Decision`. Documents land under a configurable parent folder
(`SAVE_DOCUMENT_PARENT_TITLE`, default `Shared`).

Pass `urn` only to update a document that already exists — `save_document` rejects a URN that
does not, so a made-up one fails rather than creating a document at that address.

### Step 4 — Verify the write

**Confirm the tool call actually happened before telling the user it is saved.** A model
summary claiming success is not evidence of a write. If `save_document` did not run, say the
save failed and keep the answer visible so the user does not lose it.

---

## Critical Rules

1. **Recall before capture.** Do not write a document that duplicates one already there —
   update the existing one instead.
2. **Never invent an asset, owner or URN.** If it did not come from a tool result, it does
   not go in the document.
3. **Never report a save you did not verify.** See Step 4.
4. **Ask before overwriting.** If a document with the same title exists, show the user what
   changes before replacing it.
5. **Mutations must be enabled.** `save_document` requires `TOOLS_IS_MUTATION_ENABLED=true`
   and DataHub Cloud 0.3.16+ or Core 1.4.0+. If the tool is missing, tell the user which of
   those is unmet rather than silently falling back to a description update.
6. **Keep documents short enough to read.** A document nobody finishes is a document nobody
   trusts.
