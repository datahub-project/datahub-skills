# DataHub Connector Review Skill

A Claude Code skill for reviewing DataHub connector pull requests and existing implementations against established golden standards.

## What This Skill Does

When activated, Claude becomes an expert DataHub connector reviewer that:

- **Supports two modes** - PR Review (with multi-agent analysis) and Local Audit
- **Integrates with `/review`** - Leverages Anthropic's multi-agent review for general code quality
- **Auto-loads** golden connector standards (no manual loading needed)
- **Systematically reviews** code against DataHub-specific standards
- **Identifies blockers** that would prevent PR merge
- **Provides actionable feedback** with specific fix recommendations
- **Generates structured reports** for consistent review output

## Review Modes

### PR Review Mode

For reviewing GitHub pull requests:

1. **Runs `/review`** - Multi-agent analysis (code quality, security, performance, best practices)
2. **Applies DataHub standards** - Connector-specific requirements
3. **Generates combined report** - Unified findings from both analyses

### Local Review Mode

For auditing existing code:

- Auditing an existing connector
- Reviewing code before creating a PR
- Checking compliance of work-in-progress
- Evaluating connector quality

## Quick Commands

| Command             | Mode   | Description                                  |
| ------------------- | ------ | -------------------------------------------- |
| "Review PR #123"    | PR     | Full review with /review + DataHub standards |
| "Quick PR review"   | PR     | Blockers only                                |
| "Review for merge"  | PR     | Full merge readiness assessment              |
| "Audit connector X" | Local  | Full local audit                             |
| "Check X connector" | Local  | Local audit                                  |
| "Review local code" | Local  | Audit current directory                      |
| "Check tests"       | Either | Focus on test quality                        |
| "Check types"       | Either | Focus on type safety                         |
| "Blockers only"     | Either | Critical issues only                         |

## Prerequisites

This skill requires the **pr-review-toolkit** plugin from the official Claude plugins marketplace. The skill launches specialized pr-review-toolkit agents for:

- Silent failure detection
- Test coverage analysis
- Type design review
- Code simplification suggestions

### Installing pr-review-toolkit

```bash
claude plugin install pr-review-toolkit@claude-plugins-official
```

**Verify installation:**

```bash
claude plugin list | grep pr-review-toolkit
```

## Installation

See the [top-level README](../../README.md) for installation instructions for the datahub-skills plugin.

## Review Workflow

### PR Review

```
Step 1: Multi-Agent Review
└── Run /review for general code quality

Step 2: Gather DataHub Context
├── Get PR details
├── Identify connector type
└── Identify scope of changes

Step 3: Apply DataHub Standards
├── Architecture (main.md)
├── Code Organization (patterns.md)
├── Type Safety (patterns.md)
├── Source-Specific (sql.md/api.md)
├── Lineage (lineage.md)
├── Containers (containers.md)
├── Test Quality (testing.md)
├── Security
└── Documentation

Step 4: Generate Combined Report
├── /review findings
├── DataHub standards findings
└── Overall assessment
```

### Local Review

```
Step 1: Locate Connector Files
├── Source files
├── Config files
├── Unit tests
├── Integration tests
├── Golden files
└── Documentation

Step 2: Identify Connector Type
├── Base class used
├── SQL vs API
└── Features (lineage, containers)

Step 3: Apply DataHub Standards
└── (Same as PR review)

Step 4: Generate Audit Report
├── File inventory
├── Standards compliance
├── Quality score
└── Recommendations
```

## Severity Levels

| Level          | Meaning             | Action                |
| -------------- | ------------------- | --------------------- |
| **BLOCKER**    | Violates standards  | Must fix before merge |
| **IMPORTANT**  | Significant issue   | Should fix            |
| **SUGGESTION** | Quality improvement | Optional              |
| **NOTE**       | Informational       | Awareness only        |

## Example Output

### PR Review

```markdown
## PR Review: Add DuckDB Connector

**Review Type:** New Connector
**Connector Type:** SQL Database
**Review Mode:** PR Review (multi-agent + DataHub standards)

---

### Multi-Agent Review Summary (/review)

- Code quality: Good structure, follows Python conventions
- Security: No credentials exposed
- Performance: Efficient query patterns
- Best practices: Minor improvements suggested

---

### DataHub Standards Review

**Standards Applied:** main.md, patterns.md, testing.md, sql.md

#### Critical Issues (Blockers)

1. **Missing Golden File Tests**
   - **Location:** `tests/integration/duckdb/`
   - **Standard:** `standards/testing.md` - Golden File Requirements
   - **Issue:** No golden file integration tests found
   - **Fix:** Create integration test with golden file comparison

---

**Overall Assessment:** REQUEST CHANGES
```

### Local Audit

```markdown
## Connector Audit: DuckDB

**Connector Type:** SQL Database
**Review Mode:** Local Audit
**Base Class:** TwoTierSQLAlchemySource

---

### File Inventory

| Category          | Location                               | Status  |
| ----------------- | -------------------------------------- | ------- |
| Source            | `src/.../duckdb/source.py`             | OK      |
| Config            | `src/.../duckdb/config.py`             | OK      |
| Unit Tests        | `tests/unit/.../duckdb/`               | 5 tests |
| Integration Tests | `tests/integration/duckdb/`            | OK      |
| Golden Files      | `tests/integration/duckdb/golden.json` | 12 KB   |

---

### Quality Score

| Aspect               | Score      |
| -------------------- | ---------- |
| Standards Compliance | 8/10       |
| Test Coverage        | 7/10       |
| Code Quality         | 9/10       |
| Documentation        | 6/10       |
| **Overall**          | **7.5/10** |
```

## Skill Structure

```
datahub-connector-pr-review/
├── SKILL.md           # Main skill file (review workflow, checklists)
├── README.md          # This file
├── commands/          # Skill-specific commands
├── references/        # Deep-dive review guides
├── scripts/           # Utility scripts (gather-connector-context.sh, extract_aspects.py)
└── templates/         # Report templates (full, incremental, specialized)
```

Standards are in `${CLAUDE_PLUGIN_ROOT}/standards/` (shared across skills).

## Standards Reference

| Standard        | Topics Covered                                 |
| --------------- | ---------------------------------------------- |
| `main.md`       | Base classes, SDK V2, config patterns          |
| `patterns.md`   | File organization, imports, type safety        |
| `testing.md`    | Test requirements, golden files, anti-patterns |
| `sql.md`        | SQLAlchemy sources, query patterns             |
| `api.md`        | API clients, Pydantic models, pagination       |
| `lineage.md`    | SqlParsingAggregator, view lineage             |
| `containers.md` | Container hierarchy, subtypes                  |

## Common Issues Detected

### Testing Anti-Patterns

- Trivial tests that test nothing
- Fabricated MCPs instead of real ingestion
- Excessive mocking
- Missing or tiny golden files (<5KB)

### Code Quality Issues

- Wrong base class selection
- SDK V1 usage (should be V2)
- Missing type hints
- Unsafe casts

### Architecture Issues

- Monolithic source files
- Missing config class
- Custom SQL parsing (should use SqlParsingAggregator)
- Incorrect container hierarchy

## Contributing

To improve this skill:

1. **Review process changes** → Edit `SKILL.md`
2. **Technical standards** → Edit files in `standards/`
3. **New review patterns** → Add to Common Issues section

## License

Apache 2.0 - See [LICENSE](../../LICENSE).
