# Document / Knowledge-Base Sources

**Source Type:** API-Based

## Overview

Document and knowledge-base sources ingest **unstructured content** — wiki pages,
docs, notes, and articles — from systems like Confluence, Notion, and GitHub
(Markdown files). Unlike the rest of the connector catalog, these sources do **not**
model their content as `Dataset` entities. They emit the first-class DataHub
**`document` entity** and, optionally, vector embeddings for retrieval/RAG.

There are two architectural shapes in this family. Identify which you are building
before reading further — they share an entity model but differ in almost everything
else.

| Shape                              | Examples                             | What it does                                                                                                                                        |
| ---------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — External content connector** | Confluence, Notion, GitHub Documents | Pulls content from an external system and emits `document` entities (with optional embeddings).                                                     |
| **B — Semantic enrichment source** | DataHub Documents                    | Reads `document` entities **already in DataHub**, chunks + embeds their text, and writes back only the `semanticContent` aspect. Mints no new URNs. |

## What to Extract

**Shape A (external content connectors):**

- **Documents** — pages, articles, notes (one `document` entity each)
- **Document hierarchy** — parent/child relationships via the `parentDocument` aspect and `browsePathsV2` (**not** containers)
- **Content** — page body, converted to Markdown/plain text, stored in `documentInfo.contents.text`
- **Embeddings** (optional) — vector chunks in the `semanticContent` aspect, for semantic search / RAG

**Shape B (semantic enrichment):**

- **Embeddings only** — the `semanticContent` aspect on existing `document` URNs

## Entity Model

This archetype's defining characteristic: content maps to the **`document` entity**
(`urn:li:document:...`), emitted via the `datahub.sdk.document.Document` SDK — never
to `Dataset`, and **never to `Container`**.

```
Source Concept          → DataHub Entity    → Notes
─────────────────────────────────────────────────────────────────────────
Wiki / workspace        → (browse-path root) → NOT a Container; label-only root segment
Space / database        → (browse-path node) → NOT a Container; appears in browsePathsV2
Folder                  → Document           → subtype "Folder" (Confluence) OR omitted
Page / doc / note       → Document           → no subtype, or a content subtype (e.g. "FAQ")
Page body               → documentInfo.contents.text
Page tree (parent)      → parentDocument aspect (IsChildOf relationship)
```

**URN convention:** `urn:li:document:{platform}-{stable_id}` (Notion uses
`notion-{page_id}`; Confluence uses `confluence-{instance}-{page_id}`). The id must be
**stable across runs** — derive it from the source system's immutable id, never from a
local cache path or row order.

**The instance component must be stable too.** When the URN embeds a
`platform_instance` (Confluence's `confluence-{instance}-{page_id}`), that instance id
must be derived **only from immutable properties** — never from anything that can be
rotated, renamed, or reconfigured:

- ❌ Do **not** derive it from an API token/credential, a hostname/subdomain that can
  be re-pointed (e.g. an `.atlassian.net` URL that changes on migration or vanity-domain
  setup), or any mutable config value. Confluence's fallback of hashing the URL
  (`SHA256(url)[:8]`) is a **cautionary example**: if the URL ever changes, every
  document URN changes with it, producing duplicate entities and breaking stale-entity
  removal.
- ✅ Prefer an explicit, user-supplied `platform_instance` (recommended), or a stable
  immutable identifier the source system guarantees won't change (e.g. a tenant/site GUID).
- Once chosen, the instance id is effectively permanent — changing it re-keys every URN.
  Document this clearly in the connector's config help.

**Import mode** — every Shape A connector exposes a `document_import_mode`:

- `EXTERNAL` → `Document.create_external_document(...)` — a read-only
  reference with `externalUrl` / `externalId` pointing back to the source system.
- `NATIVE` → `Document.create_document(...)` — a DataHub-native, editable document.

The default is **per-connector**: connectors mirroring an external system default to
`EXTERNAL` (Confluence, Notion), while sources whose content is effectively owned by the
pipeline default to `NATIVE` (GitHub Documents). Pick the default that matches whether the
source of truth stays external.

## Required Aspects

| Aspect                 | Required           | Description                                                                                                                                           |
| ---------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `documentKey`          | ✅ ALWAYS          | Key aspect (`id`). Derived from the source's stable id.                                                                                               |
| `documentInfo`         | ✅ ALWAYS          | `title`, `source` (NATIVE/EXTERNAL + `externalUrl`/`externalId`), `status`, `contents.text`, `created`/`lastModified` audit stamps, `parentDocument`. |
| `dataPlatformInstance` | ✅ ALWAYS          | Links the document to its data platform. **Always required.**                                                                                         |
| `subTypes`             | 🔶 WHEN MEANINGFUL | Set only when it adds value (e.g. `Folder`). Plain pages may omit it.                                                                                 |
| `browsePathsV2`        | ✅ IF HIERARCHICAL | Built from the page/space tree. Only include URNs for **in-scope** ancestors (see below).                                                             |
| `semanticContent`      | 🔶 IF EMBEDDING    | Vector chunks (`embeddings` map keyed by model). Emitted via the shared chunking subsystem.                                                           |
| `status`               | 🔄 AUTO            | Soft-delete handling via stateful ingestion.                                                                                                          |

`documentInfo` also exposes `relatedAssets` (link a doc to a Dataset/Dashboard/etc.)
and `relatedDocuments`. None of the current connectors populate these — they are an
**opportunity**, not a requirement. If your source has explicit references from a doc
to a data asset, populate `relatedAssets`.

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for the HTTP-client, pagination, and
`StatefulIngestionSourceBase` foundations. The document-specific patterns below layer
on top of it.

### Standard structure (Shape A)

```python
@platform_name("Confluence")
@config_class(ConfluenceSourceConfig)
@support_status(SupportStatus.INCUBATING)
@capability(SourceCapability.TEST_CONNECTION, "Enabled by default")
@capability(SourceCapability.DELETION_DETECTION, "Enabled by default")
@capability(SourceCapability.PLATFORM_INSTANCE, "Enabled by default")
class MyDocSource(StatefulIngestionSourceBase, TestableSource):
    platform = "my_platform"  # required for the stateful-ingestion checkpoint job_id

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        ...
```

- Extend `StatefulIngestionSourceBase` (**not** plain `Source`) and implement
  `TestableSource`. Emit through `get_workunits_internal()` so the base class wraps
  stale-entity removal around your generator.
- Declare capabilities honestly: at minimum `TEST_CONNECTION`; add
  `DELETION_DETECTION` and `PLATFORM_INSTANCE` when supported. (The reference
  connectors under-declare these — do better.)

### Platform registration (icon + branding)

Document sources register a data platform (`urn:li:dataPlatform:{platform}`) and emit
`dataPlatformInstance`, exactly like structured sources — so they need the **same
platform registration and icon**, and it is **not optional**.

→ **See [Platform Registration Guide](../platform_registration.md)** for the full
checklist (the `DataPlatform` enum, `data-platforms.yaml` entry, and a
transparent-background logo in `datahub-web-react/src/images/{platform}logo.png`).

Register the platform **consistently** — the reference connectors don't, which is a
trap to avoid:

- Confluence emits `DataPlatformInfo` (with `displayName` + `logoUrl`) **inline at
  ingestion time**, so branding appears even without the seeded registry entry.
- Notion does **not** emit `DataPlatformInfo`; it relies entirely on the frontend logo
  asset / seeded registry — so branding silently fails if that step is skipped.

Prefer the seeded registration (`data-platforms.yaml` + bundled logo) so branding does
not depend on a connector having run; emitting `DataPlatformInfo` inline is a fine
belt-and-suspenders addition. Complete platform registration **before** the connector
PR merges, so users see the icon immediately.

### Hierarchy without containers

Document hierarchy is expressed through the `parentDocument` aspect and
`browsePathsV2`, **not** `Container` entities.

- Emit a `parentDocument` URN **only if the parent is itself in the ingestion scope** —
  otherwise you create dangling references. The same in-scope rule applies to every
  `browsePathsV2` entry's URN (label-only entries with no URN are fine for
  workspace/space roots).
- If the source API only returns the _immediate_ parent (Notion), reconstruct the full
  ancestor chain from a `page_id → metadata` map built during ingestion, with a
  cycle guard. If the API returns the full ancestor array (Confluence), use it directly.
- Emit synthetic parent/folder documents **before** their children so the children can
  resolve their `parentDocument` against an existing entity.

### Content extraction

Convert the source's native format to Markdown/plain text and store it in
`documentInfo.contents.text`:

- **Hand-rolled** (Confluence): fetch `body.storage` (proprietary XHTML), strip macros
  with BeautifulSoup, convert with `markdownify`, normalize whitespace.
- **Delegated** (Notion): drive the `unstructured-ingest` pipeline and post-process its
  JSON element output. Note this couples you to a pinned third-party version and tends
  to require runtime monkeypatches for API drift — prefer hand-rolled extraction when
  the source format is tractable.

### Chunking & embeddings (shared subsystem)

Do **not** hand-roll chunking or embedding. Reuse
`datahub.ingestion.source.unstructured`:

- Config: `ChunkingConfig` (`strategy` = `by_title`|`basic`, `max_characters`,
  `overlap`, `combine_text_under_n_chars`) and `EmbeddingConfig` (`provider` =
  bedrock/cohere/openai/local/vertex_ai, `model`, `batch_size`, `rate_limit`).
- Emit via `DocumentChunkingSource.process_elements_inline(document_urn, elements)`,
  which produces one `semanticContent` MCP per document (all chunks in a single aspect,
  **not** one entity per chunk).
- **Embedding config is server-authoritative.** If the recipe doesn't set it, fetch it
  from DataHub's AppConfig and validate any local override against the server.
- Embedding failures should be reported as warnings and **not** abort the run (except
  when a hard `max_documents` limit is hit).

### Incremental processing

Avoid re-embedding unchanged documents:

- Compute a `content_hash` = `SHA256(text + processing-config fingerprint)` and store it
  as a custom property. The **config fingerprint** (chunking strategy, max chars,
  overlap, embedding provider/model, partition strategy) must be part of the hash so
  that recipe changes — not just content changes — correctly invalidate the cache.
- Bump an `EXTRACTION_ALGO_VERSION` constant when the extraction logic itself changes,
  to force reprocessing.
- This is **separate** from the framework's stale-entity removal (which soft-deletes
  documents no longer seen). Use both.

## Shape B — Semantic Enrichment Source

A specialized self-referential source (reference: `DataHubDocuments`). It reads existing
`document` entities from DataHub via `scrollAcrossEntities` (cursor-based, to avoid the
Elasticsearch 10k `max_result_window` limit), chunks + embeds their `contents.text`, and
writes back **only** the `semanticContent` aspect. It mints no new URNs and creates no
new entity types.

Distinctive patterns to follow if you build one:

- **Composition over inheritance** — instantiate `DocumentChunkingSource(standalone=False)`
  and drive it via `process_elements_inline(...)`; forward its report fields into your
  own `get_report()`.
- **Checkpoint-state seeding** — when using DataHub's stateful-ingestion checkpoints to
  track per-document hashes, **seed each new checkpoint from the last committed one**.
  Without this, the skip-set regresses every run and every document re-embeds.
- **Distributed locking** — because these sources are scheduled on short intervals but a
  full pass can outlast the interval, guard the run with a lease lock (the reference uses
  a `dataHubStepState` entity written with `EmitMode.SYNC_PRIMARY`, `If-None-Match` for
  atomic cold-start, an owner token distinct from `run_id`, and a throttled heartbeat).
  On lock-miss, skip cleanly (report a non-fatal warning), don't fail.
- **Mode duality** — optionally support a Kafka MCL event-driven mode in addition to the
  GraphQL scroll batch mode, with automatic fallback to batch when offsets/state aren't
  available. See `DataHubDocumentsSource` in
  `src/datahub/ingestion/source/datahub_documents/` for a working implementation.
- **Ownership deferral** — skip EXTERNAL documents that another pipeline already self-embeds
  (check for an existing `semanticContent` model key), unless you already own that
  document's incremental state.

## Special Considerations

- **No `Dataset`, no `Container`.** This is the single biggest difference from every other
  archetype. Reach for the `document` entity and `parentDocument`/`browsePathsV2`.
- **Rate limiting is unconfigured in the reference connectors.** Rate limiting is a general
  API-source concern — see the [Rate Limiting Pattern](../api.md) in the API-Based Sources
  Guide. It is called out here only because the reference document connectors delegate it
  entirely to their client libraries (`atlassian-python-api`, `notion-client`) with no
  configurable backoff; if your source has strict limits (Notion: 1–3 req/s), wire in
  `datahub.utilities.ratelimiter.RateLimiter` rather than inheriting that gap.
- **Stable URNs — the instance component too.** URN-id stability is a general rule (see the
  [URNs checklist](../main.md)); document sources add a wrinkle worth calling out — the
  `platform_instance` component must be derived from immutable source ids as well, never from
  rotatable/mutable properties. Confluence's `SHA256(url)` instance fallback is the cautionary
  example: a URL change re-keys every document URN, producing duplicates and breaking
  stale-entity removal.
- **Bounded error collections.** Use `LossyList`/`LossyDict` for per-document error tracking
  to avoid unbounded memory growth on large workspaces.
- **No lineage.** Document connectors don't emit table/column lineage. The nearest concept is
  `relatedAssets` (doc → asset association), currently unpopulated everywhere.

## Reports

Subclass `StaleEntityRemovalSourceReport` (Shape A) and track, at minimum: documents
scanned/processed/skipped/failed, hierarchy nodes (folders) created, `total_text_extracted_bytes`,
and embedding stats (`num_documents_with_embeddings`, `num_embedding_failures`,
`num_documents_limit_reached`). Forward embedding stats from the chunking sub-source's report
in `get_report()`.

## Example Sources in DataHub

- `src/datahub/ingestion/source/confluence/` — hand-rolled HTML→Markdown, folder synthesis, full ancestor arrays
- `src/datahub/ingestion/source/notion/` — `unstructured-ingest` pipeline, immediate-parent chain reconstruction
- `src/datahub/ingestion/source/github_documents/` — Markdown files from a Git repo
- `src/datahub/ingestion/source/datahub_documents/` — Shape B: self-referential semantic enrichment with distributed locking
- `src/datahub/ingestion/source/unstructured/` — shared chunking/embedding subsystem used by all of the above
