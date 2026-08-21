# Import Strategy: Git Repo → DataHub Documents

How to turn a git repository's files (GitHub, GitLab, Bitbucket, or self-hosted) into a hierarchy of DataHub `Document` entities — deterministically and idempotently.

---

## 1. File filter

The filter is layered. Evaluate in this precedence order for each path in the repo tree:

1. **Always skip (non-negotiable):** anything in `.git/**`, binaries/images, and any file that isn't UTF-8-decodable text. These are never importable regardless of user patterns.
2. **Include globs** — keep only paths matching the include set. Default: `**/*.{md,mdx,markdown,rst,txt}`. A user **path scope** (e.g. `docs/`) is sugar for an include glob `docs/**` intersected with the extension set.
3. **Exclude globs** — drop paths matching the exclude set. If the user supplies excludes, use them. If not, apply the **curated default denylist** below.

A path is imported iff: not always-skipped **and** matches an include **and** matches no exclude.

### Curated default exclude denylist

Applied only when the user gives no exclude patterns. Keeps real documentation, drops boilerplate and noise:

- Build / vendor / output dirs: `node_modules/**`, `dist/**`, `build/**`, `target/**`, `vendor/**`, `.venv/**`, `site/**`
- Boilerplate files: `LICENSE*`, `CHANGELOG*`

User-supplied excludes **replace** this default (they're explicit about what they want gone). User-supplied includes are intersected with the extension set unless the user explicitly widens extensions.

### Notes

- Decode as UTF-8; on decode errors, skip the file and record it as a skipped/failed entry (don't guess encodings).
- Respect the GitHub tree API `truncated` flag — if `true`, the listing is incomplete; narrow the scope or page, and warn the user.
- The preview step (SKILL.md Step 2) is where the user refines this set against the real tree — adjust includes/excludes and re-present rather than asking for patterns up front.

---

## 2. Deterministic document ID

The ID must be **stable across runs** (so re-import upserts), **URN-safe**, and **forge-agnostic** (GitHub, GitLab, Bitbucket, or self-hosted — the scheme is the same).

**Scheme:** `<host>.<repo-path>[.<file-path>]`

The `<host>.<repo-path>` prefix is the **repo namespace**, derived from the git remote. It does two things: it guarantees URN uniqueness across repos (identical file paths in different repos — even same-named repos on different forges or self-hosted instances — can never collide), and — as a bare id with no file-path suffix — it is the **repo-root folder document** (see §3).

Building the namespace from `git remote get-url origin` (works for SSH or HTTPS remotes):

1. Strip the scheme, any `user@`/credentials, and a trailing `.git`.
2. **Host** = the hostname with dots → hyphens, so it's one clean segment (`github.com` → `github-com`, `gitlab.mycorp.com` → `gitlab-mycorp-com`).
3. **Repo path** = the full project path with `/` → `.` — this preserves **GitLab subgroups** of any depth (`group/sub/project` → `group.sub.project`).
4. **File path** (for leaf/dir ids) appended with `/` → `.`, leaf extension dropped.
5. Lowercase everything; replace any char outside `[A-Za-z0-9._-]` with `-`; collapse repeated separators.

Examples:

| Remote URL                      | Path                | Document ID                                | Role                              |
| ------------------------------- | ------------------- | ------------------------------------------ | --------------------------------- |
| `github.com/acme/handbook`      | _(the repo itself)_ | `github-com.acme.handbook`                 | repo-root folder                  |
| `github.com/acme/handbook`      | `docs/setup.md`     | `github-com.acme.handbook.docs.setup`      | leaf                              |
| `gitlab.com/acme/team/sub/proj` | `docs/intro.md`     | `gitlab-com.acme.team.sub.proj.docs.intro` | leaf (subgroups preserved)        |
| `bitbucket.org/acme/repo`       | `README.md`         | `bitbucket-org.acme.repo`                  | repo-root folder (README body)    |
| `gitlab.mycorp.com/data/docs`   | `docs/setup.md`     | `gitlab-mycorp-com.data.docs.docs.setup`   | leaf (self-hosted, distinct host) |

A file id always has at least one segment after the namespace, so it can never collide with the bare repo-root id `<host>.<repo-path>`.

> Including the ref (branch/commit) in the ID is **optional and usually undesirable** — you typically want re-importing from a new commit to _update_ the same document, not create a new one. Only include the ref if the user explicitly wants per-ref documents.

**Local vs. remote produce the same IDs.** Whether you import locally (working tree) or fetch the remote, the namespace comes from the same remote URL, so the document URNs are identical — a later re-import upserts in place instead of duplicating. If a local repo has **no remote**, fall back to `local.<repo-dir-name>` as the namespace and tell the user the prefix in use.

Stamp `custom_properties = {"source_remote": "<host>/<repo-path>", "source_path": "<path>", "source_ref": "<ref>"}` on every document for traceability. For local imports, `source_ref` is the current branch/commit and you may add `"source": "local-working-tree"`.

---

## 3. Folder → hierarchy mapping

DataHub has no separate "folder" entity — a folder **is** a parent `Document`. Directories (and the repo itself) become parent documents; files become child documents.

In the rules below, `<repo-ns>` is the repo namespace from §2 (e.g. `github-com.acme.handbook`) and `<host-ns>` is its first segment, the host (e.g. `github-com`).

The node hierarchy mirrors the id structure — host → repo → directories → files — so each level's id is a dotted prefix of the next. **Container nodes (host folder, repo-root folder, directory nodes) are created with `subtype="Folder"`**; leaf documents get no structural subtype (semantic subtypes are opt-in — see SKILL.md "Subtypes").

- **Host grouping folder (default mount):** the top node is a folder with id `<host-ns>` (e.g. `github-com`), title = the host (`github.com`). All repos imported from that host nest under it. **Created idempotently** — upsert it; if it already exists from a previous import, reuse it. This is the default so the knowledge-base root stays tidy and repos are organized by forge. The host folder itself sits at the KB root, unless the user supplies a `Mount` parent (below), in which case the host folder nests under that.
  - **Opt-out:** if the user wants repos at the root as siblings (no host folder), skip this node and mount repo-root folders directly at the root / the user's mount.
- **Repo-root folder (always created):** exactly one node with id `<repo-ns>`, title = the repo name (or `host/repo-path`). `parent_document` = the host folder (default) or the mount/root (if grouping is off). The folder representing the repo; **all** other documents from this import nest under it. This is what keeps different repos from colliding in navigation — each repo is its own self-contained subtree.
  - If a **root `README.md`/`index.md`** exists, its contents become the repo-root folder's body (index convention — clicking the repo folder shows the README, matching how the forge renders it). Do **not** also create a separate `…readme` document.
  - If there's no root index file, give the repo-root folder a short synthesized stub body ("Imported from `<host>/<repo-path>`").
- **Directory node:** synthesize a parent document with id `<repo-ns>.<dir-path>` and title = the directory name (humanized). Body = a short auto-generated stub ("Documents under `docs/guides`") **unless** the directory contains an index file (below). Its `parent_document` is the enclosing directory's document (or the repo-root folder for top-level dirs).
- **Index file (`README.md` or `index.md`/`index.mdx`) inside a directory:** represents that directory. Use its contents as the directory document's body, under the directory's id (so the directory node _is_ the README). Do not also create a separate child document for the index file.
- **Leaf file:** a child document whose `parent_document` is the URN of its containing directory's document (or the repo-root folder).
- **Mount (optional override):** if the user supplies an existing parent document URN, the **host folder's** `parent_document` points to it (so you can park all forge groups under, say, an "Imported Docs" parent). The per-repo namespace guarantees uniqueness regardless of where the trees are mounted.

### Title derivation

- Prefer the first H1 (`# Heading`) in the file body, if present.
- Otherwise humanize the filename: `getting-started.md` → "Getting Started"; strip extension, replace `-`/`_` with spaces, title-case.
- Directory titles: humanize the directory name.

---

## 4. Processing order (parents first)

A child's `parent_document` URN must exist before the child is upserted. Produce the work list with a **pre-order / breadth-first** traversal of the tree so every parent precedes its children:

```
0. host grouping folder (default mount; upsert first, reused if it already exists)
1. repo-root folder (repo README or synthesized)
2. top-level directory documents
3. top-level files
4. nested directory documents (depth 2)
5. nested files (depth 2)
   ...and so on, deeper levels last
```

Within the generated script, simply sort the planned documents by path depth ascending (root = depth 0), then upsert in that order.

---

## 5. Create vs. update (idempotency)

Before executing, classify each planned document:

- **Create** — target URN does not exist (`datahub exists --urn <urn>` → false).
- **Update** — target URN exists; `upsert` will overwrite its `DocumentInfo` (title, text, parent, related assets).

This skill **never deletes**. If a file that was previously imported no longer exists in the repo, its document is left untouched — report it as "stale (not in current repo)" and suggest the user remove it via `/datahub-enrich` if desired.

---

## 6. Visibility

- **Global (default):** `show_in_global_context=True` — documents appear in search and the sidebar/knowledge navigation.
- **AI-only context:** `show_in_global_context=False` — documents are hidden from global search/sidebar and reachable only via related assets. Use when the import is meant purely as context for AI agents attached to specific datasets. In this mode, encourage supplying `related_assets`, otherwise the documents are hard to reach.

---

## 7. Related assets

If the user wants the imported docs linked to specific assets, attach `related_assets` (entity URNs) to the relevant documents. Typical patterns:

- Attach the same asset list to the **root** document only (one anchor), or
- Map specific files to specific assets when the user provides a mapping.

Resolve asset names to URNs first (use `/datahub-search` patterns or `datahub search ... --urns-only`).
