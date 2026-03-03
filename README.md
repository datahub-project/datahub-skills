# datahub-skills

Agent skills for planning and reviewing DataHub connectors. Works with [Claude Code](https://claude.ai/claude-code), [Cursor](https://cursor.sh), [Codex](https://openai.com/codex), [Copilot](https://github.com/features/copilot), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [Windsurf](https://windsurf.com), and other [Agent Skills](https://skills.sh)-compatible tools.

## What's in here

### Connector planning

Walks you through building a new DataHub connector in four steps: classify the source system type, research it (using a dedicated agent or inline), generate a `_PLANNING.md` with entity mapping and architecture, and get your sign-off before anyone writes code.

```
> Plan a connector for ClickHouse
> /connector-planning duckdb
```

### Connector review

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

### Load standards

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
> Review my connector for postgres
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
> Review my DataHub connector code
> Help me plan a new connector for DuckDB
```

#### OpenAI Codex

```bash
npx skills add datahub-project/datahub-skills -a codex
# Installs to .agents/skills/
```

```
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
> Review my DataHub connector
> Plan a new connector for BigQuery
```

#### Windsurf

```bash
npx skills add datahub-project/datahub-skills -a windsurf
# Installs to .windsurf/skills/
```

```
> Review my DataHub connector implementation
> Plan a connector for Redshift
```

#### Manual install

```bash
git clone https://github.com/datahub-project/datahub-skills.git
cp -r datahub-skills/skills/datahub-connector-pr-review  your-project/.agents/skills/
cp -r datahub-skills/skills/datahub-connector-planning   your-project/.agents/skills/
cp -r datahub-skills/skills/load-standards               your-project/.agents/skills/
```

Each skill directory is self-contained. The `standards` symlinks get dereferenced into real files on copy, so everything travels together.

### What works where

| Feature                     | Claude Code           | Cursor / Copilot / Codex / Gemini CLI / Windsurf |
| --------------------------- | --------------------- | ------------------------------------------------ |
| Planning workflow           | Yes                   | Yes                                              |
| Load standards              | Yes                   | Yes                                              |
| Review against standards    | Yes                   | Yes                                              |
| Parallel multi-agent review | Yes (5 sub-agents)    | No (runs sequentially)                           |
| Research agent delegation   | Yes (dedicated agent) | No (inline fallback)                             |
| Slash commands              | Yes                   | No (use natural language instead)                |
| Progress tracking           | Yes                   | No                                               |
| SessionStart hooks          | Yes                   | No                                               |

## Commands (Claude Code only)

Other platforms do the same things through natural language ("Review my connector", "Plan a connector for DuckDB").

| Command                             | What it does                            |
| ----------------------------------- | --------------------------------------- |
| `/connector-planning [source]`      | Plan a new connector                    |
| `/connector-review [connector]`     | Review connector code against standards |
| `/load-standards`                   | Load all 22 standards into context      |
| `/comprehensive-review [connector]` | Deep multi-agent review                 |

## Agents

| Agent                        | What it does                                              |
| ---------------------------- | --------------------------------------------------------- |
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
│   └── plugin.json
├── skills/
│   ├── datahub-connector-planning/
│   │   ├── SKILL.md
│   │   ├── standards -> ../../standards
│   │   ├── references/
│   │   └── templates/
│   ├── datahub-connector-pr-review/
│   │   ├── SKILL.md
│   │   ├── standards -> ../../standards
│   │   ├── commands/
│   │   ├── references/
│   │   ├── scripts/
│   │   └── templates/
│   └── load-standards/
│       ├── SKILL.md
│       └── standards -> ../../standards
├── agents/
│   ├── connector-researcher.md
│   ├── comment-resolution-checker.md
│   └── connector-validator.md
├── commands/
│   ├── connector-planning.md
│   ├── connector-review.md
│   └── load-standards.md
└── standards/
    ├── *.md (11 core)
    └── source_types/*.md (11 source-type)
```

The `standards` symlinks in each skill directory mean you can install a single skill and it brings its standards along. `npx skills add` dereferences these into real copies.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions and release process.

Where things live:

- Standards: `standards/`
- Review checklists: `skills/datahub-connector-pr-review/SKILL.md`
- Planning steps: `skills/datahub-connector-planning/SKILL.md`
- Agent prompts: `agents/`

## License

Apache 2.0. See [LICENSE](LICENSE).
