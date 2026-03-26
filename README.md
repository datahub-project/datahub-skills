# datahub-skills

Agent skills for working with DataHub — plan and review connectors, search the catalog, enrich metadata, trace lineage, and set up connections. Works with [Claude Code](https://claude.ai/claude-code), [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code), [Cursor](https://cursor.sh), [Codex](https://openai.com/codex), [Copilot](https://github.com/features/copilot), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [Windsurf](https://windsurf.com), and other [Agent Skills](https://skills.sh)-compatible tools.

## What's in here

### Catalog interaction skills

#### Search

Search the DataHub catalog, discover entities, and answer ad-hoc questions about your data. Supports keyword search, filtered browse, column-name search, structured property queries, and multi-step question answering.

```
> Find revenue tables in Snowflake
> Who owns the customer pipeline?
> /datahub-search datasets tagged PII
```

#### Enrich

Add or update metadata in DataHub — descriptions, tags, glossary terms, ownership, and deprecation. Shows a before/after plan and asks for approval before making changes.

```
> Add a description to the orders table
> Tag these columns as PII
> /datahub-enrich set owner of revenue_daily to @jdoe
```

#### Lineage

Explore data lineage, trace upstream sources and downstream consumers, perform impact analysis, and map cross-platform data flows.

```
> What feeds into the revenue dashboard?
> Impact analysis for changing the orders table
> /datahub-lineage trace the customer pipeline
```

#### Setup

Install the DataHub CLI, configure authentication, verify connectivity, and set up default scopes and profiles for the other interaction skills.

```
> Set up my DataHub connection
> /datahub-setup focus on Snowflake in the Finance domain
> Create a profile for the data-eng team
```

### Connector development skills

#### Connector planning

Walks you through building a new DataHub connector in four steps: classify the source system type, research it (using a dedicated agent or inline), generate a `_PLANNING.md` with entity mapping and architecture, and get your sign-off before anyone writes code.

```
> Plan a connector for ClickHouse
> /connector-planning duckdb
```

#### Connector review

Checks connector code against the 22 standards (see below). On Claude Code it runs five agents in parallel — silent failures, test coverage, type design, simplification, comment resolution. On other platforms it does the same checks one at a time.

```
> Review my connector
> /connector-review postgres
> Review PR #1234
```

If you're on Claude Code and want the parallel review, also install `pr-review-toolkit`:

```bash
claude plugin install pr-review-toolkit@claude-plugins-official
```

#### Load standards

Loads all 22 connector standards into context. Run this before starting connector work so the agent actually knows what it's checking against.

```
> Load the DataHub standards
> What are the connector standards?
```

## Installation

### Quick install (any agent)

The [Skills CLI](https://github.com/vercel-labs/skills) detects your installed agents and sets things up:

```bash
npx skills add datahub-project/datahub-skills
```

Works with most agents including Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, Cline, and Roo Code.

### Platform-specific

#### Claude Code

```bash
# Option A: Plugin install (gets you hooks, slash commands, multi-agent dispatch)
claude plugin install datahub-skills

# Also install pr-review-toolkit for multi-agent reviews:
claude plugin install pr-review-toolkit@claude-plugins-official
```

```bash
# Option B: Skills CLI (project-level, installs to .claude/skills/)
npx skills add datahub-project/datahub-skills -a claude-code
```

Then:

```
> Search for revenue tables in Snowflake
> /datahub-search who owns the customer pipeline?
> /datahub-enrich add description to orders table
> /datahub-lineage what feeds into the revenue dashboard?
> /datahub-setup verify my connection
> /connector-review snowflake
> /connector-planning duckdb
```

#### Cursor

```bash
npx skills add datahub-project/datahub-skills -a cursor
# Installs to .agents/skills/
```

Cursor picks up skills from `.agents/skills/` automatically:

```
> Search DataHub for customer tables
> Review my DataHub connector
> Plan a connector for ClickHouse
```

#### GitHub Copilot

```bash
npx skills add datahub-project/datahub-skills -a github-copilot
# Installs to .agents/skills/
```

Use in Copilot Chat:

```
> Search the DataHub catalog for revenue data
> Review my DataHub connector code
> Help me plan a new connector for DuckDB
```

#### OpenAI Codex

```bash
npx skills add datahub-project/datahub-skills -a codex
# Installs to .agents/skills/
```

```
> Find datasets owned by the data-eng team
> Review the postgres connector against DataHub standards
> Plan a connector for Snowflake
```

#### Gemini CLI

```bash
npx skills add datahub-project/datahub-skills -a gemini-cli
# Installs to .agents/skills/
```

Verify with `/skills list`, then:

```
> Who owns the revenue pipeline?
> Review my DataHub connector
> Plan a new connector for BigQuery
```

#### Windsurf

```bash
npx skills add datahub-project/datahub-skills -a windsurf
# Installs to .windsurf/skills/
```

```
> Explore lineage for the orders table
> Review my DataHub connector implementation
> Plan a connector for Redshift
```

#### Manual install

```bash
git clone https://github.com/datahub-project/datahub-skills.git

# Catalog interaction skills
cp -r datahub-skills/skills/datahub-search          your-project/.agents/skills/
cp -r datahub-skills/skills/datahub-enrich           your-project/.agents/skills/
cp -r datahub-skills/skills/datahub-lineage          your-project/.agents/skills/
cp -r datahub-skills/skills/datahub-setup            your-project/.agents/skills/
cp -r datahub-skills/skills/shared-references        your-project/.agents/skills/
cp -r datahub-skills/skills/using-datahub            your-project/.agents/skills/

# Connector development skills
cp -r datahub-skills/skills/datahub-connector-planning   your-project/.agents/skills/
cp -r datahub-skills/skills/datahub-connector-pr-review  your-project/.agents/skills/
cp -r datahub-skills/skills/load-standards               your-project/.agents/skills/
```

Each skill directory is self-contained. The `standards` symlinks get dereferenced into real files on copy, so everything travels together. The catalog interaction skills reference `shared-references/` for CLI and MCP tool documentation.

### What works where

| Feature                     | Claude Code           | Cursor / Copilot / Codex / Gemini CLI / Windsurf |
| --------------------------- | --------------------- | ------------------------------------------------ |
| Catalog search              | Yes                   | Yes                                              |
| Metadata enrichment         | Yes                   | Yes                                              |
| Lineage exploration         | Yes                   | Yes                                              |
| Connection setup            | Yes                   | Yes                                              |
| Planning workflow           | Yes                   | Yes                                              |
| Load standards              | Yes                   | Yes                                              |
| Review against standards    | Yes                   | Yes                                              |
| Parallel multi-agent review | Yes (5 sub-agents)    | No (runs sequentially)                           |
| Research agent delegation   | Yes (dedicated agent) | No (inline fallback)                             |
| Slash commands              | Yes                   | No (use natural language instead)                |
| SessionStart hooks          | Yes (via plugin)      | No                                               |

## Commands (Claude Code only)

Other platforms do the same things through natural language.

### Catalog interaction

| Command                          | What it does                                    |
| -------------------------------- | ----------------------------------------------- |
| `/catalog-search [query]`        | Search the catalog and answer questions          |
| `/catalog-enrich [entity]`       | Add or update metadata                           |
| `/catalog-lineage [entity]`      | Explore lineage and trace dependencies           |
| `/catalog-setup [task]`          | Set up connection and configure defaults         |

### Connector development

| Command                             | What it does                            |
| ----------------------------------- | --------------------------------------- |
| `/connector-planning [source]`      | Plan a new connector                    |
| `/connector-review [connector]`     | Review connector code against standards |
| `/load-standards`                   | Load all 22 standards into context      |

## Agents

| Agent                        | What it does                                              |
| ---------------------------- | --------------------------------------------------------- |
| `metadata-searcher`          | Fast sub-agent for executing catalog queries (Claude Code)|
| `connector-researcher`       | Researches source systems before you write a connector    |
| `connector-validator`        | Runs validation scripts and reports results               |
| `comment-resolution-checker` | Checks whether PR review comments were actually addressed |

## Standards

22 standards live in `standards/`, split into two groups:

**Core (11):** main, api, sql, code_style, containers, lineage, patterns, performance, platform_registration, registration, testing

**Source-type (11):** bi_tools, data_lakes, data_warehouses, identity_platforms, ml_platforms, nosql_databases, orchestration_tools, product_analytics, query_engines, sql_databases, streaming_platforms

## Repo layout

```
datahub-skills/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── skills/
│   ├── datahub-search/              # Catalog search and discovery
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── templates/
│   ├── datahub-enrich/              # Metadata enrichment
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── templates/
│   ├── datahub-lineage/             # Lineage exploration
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── templates/
│   ├── datahub-setup/               # Connection setup and config
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── templates/
│   ├── datahub-connector-planning/  # Connector planning
│   │   ├── SKILL.md
│   │   ├── standards -> ../../standards
│   │   ├── references/
│   │   └── templates/
│   ├── datahub-connector-pr-review/ # Connector review
│   │   ├── SKILL.md
│   │   ├── standards -> ../../standards
│   │   ├── commands/
│   │   ├── references/
│   │   ├── scripts/
│   │   └── templates/
│   ├── load-standards/              # Load connector standards
│   │   ├── SKILL.md
│   │   └── standards -> ../../standards
│   ├── shared-references/           # Shared CLI docs
│   │   └── datahub-cli-reference.md
│   └── using-datahub/              # Routing table (injected at session start)
│       └── SKILL.md
├── agents/
│   ├── connector-researcher.md
│   ├── comment-resolution-checker.md
│   └── connector-validator.md
├── commands/
│   ├── catalog-search.md
│   ├── catalog-enrich.md
│   ├── catalog-lineage.md
│   ├── catalog-setup.md
│   ├── connector-planning.md
│   ├── connector-review.md
│   └── load-standards.md
└── standards/
    ├── *.md (11 core)
    └── source_types/*.md (11 source-type)
```

The `standards` symlinks in each connector skill directory mean you can install a single skill and it brings its standards along. `npx skills add` dereferences these into real copies.

The catalog interaction skills share reference documents in `shared-references/` for CLI syntax, MCP tool signatures, and the DataHub entity model.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions and release process.

Where things live:

- Catalog interaction skills: `skills/datahub-search/`, `skills/datahub-enrich/`, `skills/datahub-lineage/`, `skills/datahub-setup/`
- Shared references: `skills/shared-references/`
- Connector standards: `standards/`
- Review checklists: `skills/datahub-connector-pr-review/SKILL.md`
- Planning steps: `skills/datahub-connector-planning/SKILL.md`
- Agent prompts: `agents/`

## License

Apache 2.0. See [LICENSE](LICENSE).
