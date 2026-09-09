# DataHub Privacy Operations

Build an evidence-backed privacy impact map and approval-ready operations plan from DataHub
schema, lineage, ownership, tags, glossary terms, and structured properties.

```text
> Trace the downstream PII footprint for this erasure request
> Prepare a dry-run plan and preserve any legal holds
> Record the verified outcome in DataHub after I approve the write-back scope
```

The skill keeps DataHub in its correct role as the metadata control plane. It never claims that
DataHub deleted source-system rows. Any data-plane action requires a named external executor,
scope-bound approval, and postcondition receipt. DataHub metadata write-back has a second approval
boundary and must be verified from a fresh read-only MCP session.
