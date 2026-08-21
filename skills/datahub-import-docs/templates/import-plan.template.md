# Import Plan

**Source:** <local working tree of OWNER/REPO @ BRANCH | github.com/OWNER/REPO @ REF>
**Scope:** <whole repo | subdirectory PATH>
**Include:** <globs (default `**/*.{md,mdx,markdown,rst,txt}`)>
**Exclude:** <globs | curated default denylist>
**Mount:** group by host → HOST (default) | root | under PARENT_URN
**Visibility:** <global (searchable) | AI-only context (show_in_global_context=False)>
**Related assets:** <none | URN list>
**Documents:** <N> total — <C> create, <U> update (re-import), 0 delete

## Hierarchy preview

```text
HOST                             → host folder (<host-ns> · created/reused)
└── HOST/REPO-PATH               → repo folder (<repo-ns> · body = root README)
    ├── docs/                     → "Docs" (folder)
    │   ├── setup.md              → "Setup"
    │   └── guides/               → "Guides" (folder)
    │       └── intro.md          → "Intro"
```

## Documents

(`<host-ns>` = host segment, e.g. `github-com`; `<repo-ns>` = full namespace, e.g. `github-com.acme.handbook`)

| #   | Path          | → Title   | Document ID (urn suffix) | Parent           | Subtype | Action       |
| --- | ------------- | --------- | ------------------------ | ---------------- | ------- | ------------ |
| 0   | _(host)_      | HOST      | `<host-ns>`              | <mount/root>     | Folder  | create/reuse |
| 1   | _(repo)_      | HOST/REPO | `<repo-ns>`              | `<host-ns>`      | Folder  | create       |
| 2   | docs/         | Docs      | `<repo-ns>.docs`         | `<repo-ns>`      | Folder  | create       |
| 3   | docs/setup.md | Setup     | `<repo-ns>.docs.setup`   | `<repo-ns>.docs` | —       | create       |

## Notes

- **Folder subtype:** container nodes (host, repo, directories) are typed `Folder`; leaf docs are untyped unless you opt into semantic subtypes (Runbook/FAQ — surveyed from the catalog first).
- **Grouped by host:** repos nest under a per-host folder (`<host-ns>`), created once and reused across imports from the same forge.
- **Repo as folder:** each repo is one folder document (`<repo-ns>`); everything nests under it, so different repos — even same-named ones on different hosts — never collide.
- **Idempotency:** IDs are deterministic from repo + path, so re-import updates in place (no duplicates).
- **Skipped:** <count + reasons — binaries, non-text, decode errors>
- **Truncated:** <yes/no — remote only; if yes, the listing is incomplete and scope is partial>
- **Stale (in DataHub, not in repo):** <none | list — left untouched>

---

**Confirm:** This will import **<N> documents** (<C> new, <U> updated) from `<OWNER>/<REPO>`. Proceed?
