# DataHub Connector Planning Skill

A Claude Code skill for planning new DataHub connectors — from initial research through a complete planning document ready for implementation.

## What This Skill Does

When activated, Claude guides you through a 4-step interactive planning process:

1. **Classify** the source system (SQL database, API, streaming, etc.)
2. **Research** the source using the connector-researcher agent (docs, SDKs, similar connectors)
3. **Create a planning document** with entity mapping, architecture decisions, config design, and testing strategy
4. **Get your approval** before implementation begins

## Output

The skill produces a `_PLANNING.md` document containing:

- Source system overview and classification
- Entity mapping table (source concepts → DataHub entities)
- Architecture decisions (base class, config, client design)
- Capabilities to implement
- Configuration design
- Testing strategy
- Known limitations
- Implementation order

## Quick Commands

| Command                         | Description            |
| ------------------------------- | ---------------------- |
| "Plan a connector for DuckDB"   | Full planning workflow |
| "Research Snowplow for DataHub" | Research phase only    |
| "New DataHub connector for X"   | Full planning workflow |
| `/connector-planning postgres`  | Via slash command      |

## Prerequisites

- Working in a DataHub repository clone (for finding similar connectors during research)
- Internet access (for researching source system documentation)

## Skill Structure

```
datahub-connector-planning/
├── SKILL.md           # Main skill file (4-step planning workflow)
├── README.md          # This file
├── references/        # Technical reference documents
│   ├── source-type-mapping.yml    # Source category classification
│   ├── two-tier-vs-three-tier.md  # SQL base class selection guide
│   ├── capability-mapping.md      # Feature → @capability mapping
│   ├── testing-patterns.md        # Test structure and golden files
│   └── mce-vs-mcp-formats.md     # Output format guide
└── templates/         # Document templates
    ├── planning-doc.template.md            # Main planning doc structure
    └── implementation-summary.template.md  # Quick implementation reference
```

## Example Workflow

```
User: "I want to build a DataHub connector for ClickHouse"

Claude: Classifies ClickHouse as SQL Database (two-tier)
      → Launches connector-researcher agent
      → Presents research findings
      → Asks about test environment, permissions, feature scope

User: "I have a local ClickHouse instance. I want basic metadata + lineage."

Claude: Loads golden standards (main.md, sql.md, containers.md, etc.)
      → Creates _PLANNING.md with:
        - TwoTierSQLAlchemySource base class
        - Database/Schema/Table/View entity mapping
        - ClickHouse SQLAlchemy dialect configuration
        - Unit + integration test plan
        - Implementation order
      → Presents summary for approval

User: "LGTM"

Claude: Plan approved. Ready for implementation.
```

## License

Apache 2.0 - See [LICENSE](../../LICENSE).
