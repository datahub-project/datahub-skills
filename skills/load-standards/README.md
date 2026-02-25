# Load Standards Skill

Load all 22 DataHub connector golden standards into context, ready for connector development or review.

## What This Skill Does

Reads all golden standard files and provides a summary of what's loaded. Use this before starting any connector work to ensure the agent has full standards context.

## Quick Commands

| Command                             | Description                          |
| ----------------------------------- | ------------------------------------ |
| "Load the DataHub standards"        | Load all 22 standards                |
| "What are the connector standards?" | Load and summarize                   |
| "Load golden standards"             | Load all standards                   |
| `/load-standards`                   | Via slash command (Claude Code only) |

## Standards Loaded

### Core Standards (8 files)

`main.md`, `patterns.md`, `code_style.md`, `testing.md`, `containers.md`, `performance.md`, `registration.md`, `platform_registration.md`

### Interface Standards (3 files)

`sql.md`, `api.md`, `lineage.md`

### Source-Type Standards (11 files)

`sql_databases.md`, `data_warehouses.md`, `query_engines.md`, `data_lakes.md`, `bi_tools.md`, `orchestration_tools.md`, `streaming_platforms.md`, `ml_platforms.md`, `identity_platforms.md`, `product_analytics.md`, `nosql_databases.md`

## Skill Structure

```
load-standards/
├── SKILL.md        # Main skill file
├── README.md       # This file
└── standards/      # Symlink to ../../standards (dereferenced on install)
```

## License

Apache 2.0 - See [LICENSE](../../LICENSE).
