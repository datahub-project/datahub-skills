# Safety and Write-Back Policy

## Read-Only Investigation

Normal analysis may resolve entities, inspect schema/metadata, and traverse
lineage. It must not request or call mutation tools. Preview is also read-only.

Do not fabricate metadata, owners, tags, glossary terms, quality, usage,
approvals, lineage, or write-back outcomes. Do not leak credentials, access
tokens, prompts, or raw secret-bearing responses. Do not present inferred
criticality as explicit DataHub metadata.

## Mutation Gate

Write-back is allowed only when all conditions hold:

1. Mutations are enabled in runtime configuration.
2. The analysis ID resolves to a completed, unexpired server-side record.
3. The user saw the exact preview.
4. The user supplied explicit human confirmation after that preview.
5. The target is the reviewed root asset.

Treat client-provided scores, decisions, approvals, or record content as
untrusted. Rebuild the write from the stored completed analysis.

## Mutation Scope

- Write only to the reviewed root asset.
- Do not modify downstream assets.
- Do not change owners, tags, glossary terms, quality, or usage.
- Do not replace unrelated documentation.
- Preserve existing documentation and manage only the analysis-specific block.
- Keep the operation idempotent where practical.

Use analysis-specific delimiters when documentation is the mutation mechanism:

```text
<!-- DATAHUB-SCHEMA-REVIEW:BEGIN <analysis-id> -->
...
<!-- DATAHUB-SCHEMA-REVIEW:END <analysis-id> -->
```

## Required Record

Record analysis ID and UTC timestamp, proposed change, column and new value,
decision, deterministic score/level, unique affected count, real approvals,
concise evidence, migration/rollback summaries, and the statement **No migration
SQL was executed.**

Never execute migration SQL.

## Verification and Recovery

Re-read the root after the mutation and compare the exact managed section.
Return a structured receipt. Repeating the same write should be a no-op when the
section already matches.

On a timeout or transport error after submission, report the outcome as unknown.
Do not claim success or retry automatically. Ask the user to inspect DataHub.
Remove a test record by deleting only its matching managed block or by using the
documented DataHub revert action when the entire editable override should be
removed.
