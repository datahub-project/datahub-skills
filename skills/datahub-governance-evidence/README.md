# DataHub Governance Evidence

Collect a systematic, scoreless summary of governance metadata visible in
DataHub. The skill covers ownership, documentation, domains, classifications,
lineage, and qualified Structured Properties. It can optionally align the same
observations to project-authored framework review objectives without making a
compliance or certification determination.

## What it does

1. Fixes and records the catalog scope
2. Collects metadata through DataHub MCP tools or the CLI
3. Assigns mechanical `observed`, `not observed`, or `unable to determine`
   states
4. Produces matching Markdown and structured JSON packages
5. Optionally maps observations to narrow CSA AICM, GDPR, HIPAA, ISO/IEC
   27001, ISO/IEC 42001, and SOC 2 review objectives
6. Routes optional metadata improvements through a separate, human-approved
   enrichment workflow

## Usage

```
/datahub-governance-evidence review ownership and documentation for production datasets
/datahub-governance-evidence collect scoreless governance evidence for the Finance domain
/datahub-governance-evidence show which selected datasets have retention intent recorded
/datahub-governance-evidence align catalog evidence to selected ISO/IEC 27001 and SOC 2 objectives
```

Or ask naturally: "Create a governance evidence package from DataHub for our
Snowflake production datasets."
