# DataHub Schema-Change Certification

Certify risky dataset field renames, drops, and type changes with exact DataHub context, a validated expand-migrate-contract package, scope-bound human approval, and durable metadata read-back.

## Use it for

- a schema-change decision, not only exploratory impact analysis;
- exact downstream path and observed-usage evidence;
- a staged dbt delivery package with structural validation;
- an immutable approval scope and SHA-256 passport;
- idempotent DataHub decision write-back.

## Safety properties

- Live and fixture evidence never collapse into one claim.
- Exact target cardinality, large schemas, and lineage paths must have complete pagination evidence.
- Only an exact policy-whitelisted live boundary can prepare mutations; fixture, unavailable, and unknown boundaries remain `NOT_RUN` with zero operations.
- Live query usage is rebuilt from hash-bound raw MCP pages; an inspected successful zero is distinct from a missing call.
- Metadata and query SQL are treated as untrusted data, never instructions.
- Risk, tool preflight, and artifact manifests are recomputed from their authoritative inputs before scope construction.
- Credential-shaped keys and values are rejected without echo before they can enter artifacts, approval, or a passport.
- The initial request is never mutation approval; the reviewer approves an exact scope hash.
- Mutation tool schemas and optional structured-property definitions are checked before execution.
- Mutation receipts remain incomplete until exact durable state is read back.

## Requirements

- Python 3.11+ for `scripts/certify_change.py`;
- a configured official DataHub MCP server for live execution; CLI-only sessions remain `NOT_RUN` rather than falling back to simulated evidence;
- host-exposed mutation tools for write-back;
- repository and dbt context before generated code can be marked structurally valid.

Resolve the helper from the installed skill directory instead of assuming the current working directory. Claude Code can use `${CLAUDE_SKILL_DIR}/scripts/certify_change.py`; other agents should use their resolved absolute skill path. Commands use `python3` on POSIX systems and `python` on Windows when it resolves to Python 3.11 or newer.

The bundled `references/policy-v1.json` is a versioned reference default, not an official universal DataHub risk standard. Operators may select a reviewed custom policy before starting a run; the selected policy hash then remains authoritative for scope and passport verification.

Plain lineage questions belong to `/datahub-lineage`; ordinary metadata edits belong to `/datahub-enrich`.

## Example prompts

```text
Certify renaming customer_email to contact_email on this DataHub dataset. Prepare a staged migration, but do not write anything until I approve the exact scope hash.
```

```text
What will break if we drop legacy_customer_id, and can you produce a reviewable certification package?
```

```text
Prepare a type-change passport for order_total from string to decimal. Keep warehouse execution NOT_RUN.
```

See [`SKILL.md`](SKILL.md) for the workflow and [`references/evidence-contract.md`](references/evidence-contract.md) for machine contracts.
