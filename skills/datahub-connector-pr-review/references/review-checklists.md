# Review Checklists

## Contents

- [Architecture Review](#architecture-review)
- [Code Organization Review](#code-organization-review)
- [Python Code Quality Review](#python-code-quality-review)
- [Type Safety Review](#type-safety-review)
- [Source-Type Specific Review](#source-type-specific-review)
- [Lineage Review](#lineage-review)
- [Container Review](#container-review)
- [Performance and Scalability Review](#performance-and-scalability-review)
- [Test Quality Review](#test-quality-review)
- [Security Review](#security-review)
- [Documentation Review](#documentation-review)

Apply these checks based on connector type. Reference standards files for details.

## Architecture Review

**Detailed procedures in `references/architecture-review.md`**

Quick checklist:

- [ ] Correct base class for source type (see `standards/main.md`)
- [ ] SDK V2 usage throughout
- [ ] Separate config, client, source classes
- [ ] No circular dependencies
- [ ] Clear data flow: config -> client -> extraction -> emission

Use context gathering script (validate connector name is alphanumeric before use): `./scripts/gather-connector-context.sh "${CONNECTOR_NAME}"`

---

## Code Organization Review

Check against `standards/patterns.md`:

- [ ] File organization matches standards
- [ ] Proper imports and dependencies
- [ ] Config classes in separate file
- [ ] No circular dependencies

---

## Python Code Quality Review

**Detailed procedures in `references/python-quality-review.md`**

Check against `standards/code_style.md`.

---

## Type Safety Review

Check against `standards/code_style.md` type safety section.

## Source-Type Specific Review

**For SQL sources** (check `standards/sql.md`):

- [ ] Proper SQLAlchemy usage
- [ ] Query patterns follow standards
- [ ] Schema introspection approach
- [ ] Connection handling

**For API sources** (check `standards/api.md`):

- [ ] Separate API client class
- [ ] Pydantic models for responses
- [ ] Error handling and retries
- [ ] Pagination handling

## Lineage Review

Check against `standards/lineage.md`:

- [ ] Uses SqlParsingAggregator (not custom parsing)
- [ ] Proper lineage entity construction
- [ ] Column-level lineage (if supported)

## Container Review

Check against `standards/containers.md`:

- [ ] Correct container hierarchy
- [ ] Proper parent-child relationships
- [ ] Correct subtypes (Database, Schema, etc.)

---

## Performance and Scalability Review

**Detailed procedures in `references/performance-review.md`**

Quick checklist:

- [ ] Uses generators (`yield`) for workunit emission
- [ ] No N+1 query patterns (batch per schema, not per table)
- [ ] HTTP session reuse (API sources)
- [ ] Pagination implemented for large results
- [ ] No unbounded in-memory collections

Key question: "How many API calls/queries for 1,000 tables?"

---

## Test Quality Review

Check against `standards/testing.md`:

- [ ] Unit tests exist and are meaningful
- [ ] Integration tests with golden files
- [ ] Golden file is non-trivial (>5KB, >20 events)
- [ ] Tests are NOT trivial (see anti-patterns)
- [ ] No fabricated test data

**Use `extract_aspects.py` to analyze golden files:**

```bash
python ./scripts/extract_aspects.py <golden_file.json>
```

Verify the golden file contains expected aspects:

- [ ] `schemaMetadata` present for all datasets (may be in MCE/proposedSnapshot format)
- [ ] `container` aspect linking datasets to parent containers
- [ ] `subTypes` distinguishing Tables from Views
- [ ] `upstreamLineage` for views (if lineage is implemented)
- [ ] `viewProperties` with view definitions (for views)

## Security Review

- [ ] No hardcoded credentials
- [ ] No secrets in test files (except Docker test containers)
- [ ] Proper credential handling
- [ ] No SQL injection vulnerabilities

## Documentation Review

- [ ] Docstrings on public classes/methods
- [ ] Config options documented
- [ ] Example recipes provided

---
