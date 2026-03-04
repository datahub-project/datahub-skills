# DataHub Connector Community Feedback Skill

A guided field-testing experience for DataHub community members who want to test a connector against their real environment and share structured feedback with connector authors.

## What This Skill Does

Code reviewers can catch standards violations, but only real users can catch:

- Coverage gaps in production data environments
- Authentication and permissions complexity
- Performance and behavior at scale
- Whether cross-platform lineage works for specific data stacks
- Accuracy of the documentation

This skill walks community members through a structured, 7-phase testing session and helps them share feedback as a PR comment, GitHub Issue, and/or local report.

## Quick Start

```
> I want to test the Snowflake connector from PR #1234
> /connector-community-feedback
> Help me give feedback on the DuckDB connector
```

## What Gets Covered

| Area | What's Evaluated |
|------|-----------------|
| **Setup** | Installation experience, time to first ingest |
| **Configuration** | Intuitiveness, missing options, docs accuracy |
| **Authentication** | Role setup complexity, credential handling |
| **Asset coverage** | Tables, views, schemas — expected vs. found |
| **Feature support** | Schema, lineage, profiling, usage, tags, owners |
| **Edge cases** | Errors, unexpected behavior, scale concerns |
| **Cross-platform lineage** | Which scenarios work, which are out of scope |

## Testing Modes

### DataHub Quickstart (local Docker)

Best for: first impressions, installation experience, UI validation, feature coverage.
We'll spin up DataHub locally together so you can see what gets ingested.

### Your DataHub instance (production or staging)

Best for: real-world asset coverage, performance at scale, edge cases, authentication.
You ingest into your own environment — the agent generates a credential-safe recipe and can run ingestion on your behalf.

### No live instance (guided walkthrough)

Best for: exploring the config and documentation experience without running ingestion.

## Security & Credentials

This skill is designed to never handle your credentials. All recipes use environment variable references (`${ENV_VAR}`), and you set real values in your terminal. The agent can run `datahub ingest` without ever seeing your passwords or tokens.

**If you accidentally paste credentials into the chat:** stop and revoke/rotate them immediately.

## Output Options

After testing, you can:

1. **Save a full report locally** — `connector-feedback-[name]-[date].md`
2. **Post a condensed summary as a PR comment** — includes feature matrix and verdict
3. **Create a GitHub Issue** — for bugs found, or for testing already-merged connectors

You always see the full report and get to approve it before anything is posted to GitHub.

## 7-Phase Workflow

```
Phase 1: Discovery
└── Fetch PR details or identify connector version

Phase 2: Tester Profile
├── Source system deployment type
├── Version / edition
├── DataHub environment
└── Cross-platform lineage use cases

Phase 3: Testing Mode + Scope
├── Choose: Quickstart / production / no instance
├── Select: which assets and features to test
├── Validate: lineage prerequisites
└── Generate: focused ingestion config

Phase 4: Pre-flight + Install + Config
├── Environment checks (automated where possible)
├── Install connector
├── Credential safety warning
├── Generate ${ENV_VAR} recipe
└── Run ingestion (agent-executed, no secrets exposed)

Phase 5: Verification Checklist
└── Pre-generated pass/fail scenarios in the DataHub UI

Phase 6: Structured Feedback
├── Setup & installation experience
├── Configuration & authentication
├── Asset coverage (production path)
├── Feature assessment
├── Edge cases & issues
└── Overall assessment

Phase 7: Output
├── Preview full report
├── Save locally
├── Post to PR
└── Create GitHub Issue
```

## Installation

See the [top-level README](../../README.md) for installation instructions.

## Skill Structure

```
datahub-connector-community-feedback/
├── SKILL.md           # Main skill file (7-phase workflow, credential safety)
├── README.md          # This file
└── templates/
    ├── feedback-report.md   # Full local report template
    └── pr-comment.md        # Condensed PR comment template
```

## License

Apache 2.0 — See [LICENSE](../../LICENSE).
