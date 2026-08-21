# Document SDK Reference

How to create and persist DataHub **Document** entities using the stable Python SDK shipped in `acryl-datahub` **v1.6.0+**. This is the only write path this skill uses — no server-side import resolvers, no experimental GraphQL mutations.

> Verify availability: `python3 -c "from datahub.sdk import Document, DataHubClient; print('ok')"`. If this fails, the CLI is too old (< 1.6.0) — upgrade before proceeding.

---

## Client

```python
from datahub.sdk import DataHubClient, Document

# Reads DATAHUB_GMS_URL / DATAHUB_GMS_TOKEN, then falls back to ~/.datahubenv
client = DataHubClient.from_env()

# Or pass explicitly:
# client = DataHubClient(server="http://localhost:8080", token="<pat>")
```

---

## Creating a native document

`Document.create_document` stores the full text inside DataHub (indexed for search). This is what you use for files imported from a GitHub repo.

```python
doc = Document.create_document(
    id="github-com.acme.handbook.docs.setup",      # deterministic → urn:li:document:<id>
    title="Setup",
    text="# Setup\n\nInstall steps...",      # markdown body (file contents)
    status="PUBLISHED",                       # or "UNPUBLISHED"
    show_in_global_context=True,              # False = AI-only context (reachable via assets)
    subtype="Reference",                      # optional: Runbook / FAQ / Tutorial / Reference
    parent_document="urn:li:document:github-com.acme.handbook.docs",  # optional hierarchy
    related_assets=[                           # optional asset links
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.orders,PROD)"
    ],
    related_documents=None,                    # optional sibling/related doc URNs
    owners=None, tags=None, terms=None, domain=None,
    custom_properties={"source_repo": "acme/handbook", "source_path": "docs/setup.md"},
)
```

**Key arguments** (all keyword-only):

| Arg                      | Type             | Notes                                                               |
| ------------------------ | ---------------- | ------------------------------------------------------------------- |
| `id`                     | `str` (required) | Becomes `urn:li:document:<id>`. Must be deterministic & URN-safe.   |
| `title`                  | `str` (required) | Display name.                                                       |
| `text`                   | `str` (required) | Markdown body.                                                      |
| `status`                 | `str`            | `"PUBLISHED"` (default) or `"UNPUBLISHED"`.                         |
| `show_in_global_context` | `bool`           | `True` (default) = search + sidebar; `False` = AI-only context.     |
| `subtype`                | `str?`           | Free-form sub-type label.                                           |
| `parent_document`        | `str?`           | Parent document URN (hierarchy).                                    |
| `related_assets`         | `list[str]?`     | Entity URNs (datasets, dashboards, etc.).                           |
| `related_documents`      | `list[str]?`     | Other document URNs.                                                |
| `custom_properties`      | `dict[str,str]?` | Useful for stamping `source_repo` / `source_path` for traceability. |

---

## Creating an external document reference

For docs that live in another system (Notion, Confluence, Google Docs) where you want a DataHub reference rather than a stored copy. Not the default path for GitHub import, but available.

```python
doc = Document.create_external_document(
    id="notion.team-handbook",
    title="Team Handbook",
    platform="notion",                         # or "urn:li:dataPlatform:notion"
    external_url="https://notion.so/team-handbook",
    external_id="abc123",                      # optional id in the source system
    text="Optional summary for indexing",      # optional
    show_in_global_context=True,
)
```

---

## Persisting: upsert (idempotent)

```python
# Idempotent: creates if absent, updates in place if the URN already exists.
client.entities.upsert(doc)

# Strict create (errors if the URN already exists) — avoid for re-import.
# client.entities.create(doc)
```

**Always use `upsert` for imports.** Combined with deterministic `id`s, re-running an import updates documents in place instead of creating duplicates.

---

## Reading back / verifying

```python
from datahub.metadata.urns import DocumentUrn
existing = client.entities.get(DocumentUrn("github-com.acme.handbook.docs.setup"))
print(existing.title)
```

Or from the CLI:

```bash
datahub get --urn "urn:li:document:github-com.acme.handbook.docs.setup"
datahub search "*" --where "entity_type = document" --limit 10
```

---

## Checking existence (for the create-vs-update plan)

```bash
datahub exists --urn "urn:li:document:github-com.acme.handbook.docs.setup"
```

Or in Python: `client.entities.get(...)` inside a try/except, or a search over `entity_type = document`.

---

## Ordering rule

A child document's `parent_document` URN **must already exist** when the child is upserted. Always process parent (directory / index) documents before their children. See `import-strategy.md` for the deterministic ordering.

---

## Why this is PR-independent

DataHub's document _import UI features_ (file upload, GitHub browser, preview) are implemented as server-side GraphQL resolvers. Those may or may not exist on a given server. The `Document` entity, its aspects (`DocumentInfo`, `DocumentKey`, `DocumentContents`, `DocumentSettings`), and the `datahub.sdk.Document` API are part of the **shipped metadata model and SDK (v1.6.0)**. By constructing documents in the agent and writing them through `upsert`, this skill produces the same outcome (a hierarchy of linked, idempotent documents) without calling any import-specific resolver.
