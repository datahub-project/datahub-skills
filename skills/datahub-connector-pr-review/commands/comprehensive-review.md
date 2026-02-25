---
name: comprehensive-review
description: Run a comprehensive multi-agent review of DataHub connector code using specialized agents in parallel
arguments:
  - name: connector
    description: Name of the connector to review (e.g., "postgres", "snowflake")
    required: false
  - name: mode
    description: "Execution mode: 'parallel' (faster) or 'sequential' (detailed)"
    required: false
    default: parallel
  - name: agents
    description: "Comma-separated agents to run: silent-failures,tests,types,simplify,all"
    required: false
    default: all
---

# Comprehensive Multi-Agent Connector Review

You are orchestrating a comprehensive code review using specialized agents. This provides deeper analysis than a single-pass review by using focused experts for different aspects of code quality.

## Available Agents

| Agent                          | Focus Area                    | Key Findings                                   |
| ------------------------------ | ----------------------------- | ---------------------------------------------- |
| **silent-failure-hunter**      | Error handling, logging       | Silent failures, missing error context         |
| **test-analyzer**              | Test coverage, quality        | Trivial tests, coverage gaps (priority 1-10)   |
| **type-design-analyzer**       | Types, Pydantic models        | Type safety issues (scores 1-10 per dimension) |
| **code-simplifier**            | Complexity, readability       | Refactoring opportunities                      |
| **comment-resolution-checker** | Review comment follow-through | Unaddressed comments, suspicious resolutions   |

## Execution Workflow

### Step 1: Determine Scope

If connector specified:

```bash
# Get connector files
./scripts/gather-connector-context.sh {{connector}} [datahub_repo_path]
```

If no connector (PR review):

```bash
# Get changed files
git diff --name-only main
```

### Step 2: Launch Agents

**Mode: Parallel (default)**
Launch all selected agents simultaneously using the Task tool with multiple tool calls in a single message. This is faster but produces separate reports.

**Mode: Sequential**
Run agents one at a time, allowing each to complete before the next. This allows findings from one agent to inform others.

### Step 3: Agent Selection

Based on `agents` argument:

- `all` → Run all 5 agents
- `silent-failures` → Run silent-failure-hunter only
- `tests` → Run test-analyzer only
- `types` → Run type-design-analyzer only
- `simplify` → Run code-simplifier only
- `comments` → Run comment-resolution-checker only
- `silent-failures,tests` → Run specified combination

### Step 4: Aggregate Results

Combine findings from all agents into a unified report.

## Orchestration Instructions

### For Parallel Mode

Use the Task tool to launch multiple agents simultaneously in a single message:

```
Task tool (call 1):
  subagent_type: pr-review-toolkit:silent-failure-hunter
  prompt: "Review [files] for silent failures, swallowed exceptions, missing error logging..."

Task tool (call 2):
  subagent_type: pr-review-toolkit:pr-test-analyzer
  prompt: "Analyze test coverage for [connector], find trivial tests, coverage gaps..."

Task tool (call 3):
  subagent_type: pr-review-toolkit:type-design-analyzer
  prompt: "Review type design in [files], check Pydantic models, type hints..."

Task tool (call 4):
  subagent_type: pr-review-toolkit:code-simplifier
  prompt: "Identify simplification opportunities in [files], check for DRY violations..."

Task tool (call 5):
  subagent_type: datahub-skills:comment-resolution-checker
  prompt: "Check whether all review comments on PR #[pr] in [owner/repo] have been substantively addressed..."
```

**Important:** All 5 Task tool calls should be made in a single message to run them in parallel.

### For Sequential Mode

Run agents one at a time, passing context between them:

1. Run comment-resolution-checker first (identifies unaddressed feedback to prioritize)
2. Run silent-failure-hunter second (finds error handling issues)
3. Run test-analyzer third (may find tests missing for error paths)
4. Run type-design-analyzer fourth (validates types)
5. Run code-simplifier last (suggests final polish)

## Unified Report Format

After all agents complete, produce this unified report:

```markdown
# Comprehensive Review: [Connector Name]

**Date:** [date]
**Mode:** Parallel | Sequential
**Agents Run:** [list]
**Files Analyzed:** [count]

---

## Executive Summary

| Agent              | Issues Found | Critical | High  | Medium |
| ------------------ | ------------ | -------- | ----- | ------ |
| Comment Resolution | X            | Y        | Z     | W      |
| Silent Failures    | X            | Y        | Z     | W      |
| Test Gaps          | X            | Y        | Z     | W      |
| Type Issues        | X            | Y        | Z     | W      |
| Complexity         | X            | Y        | Z     | W      |
| **Total**          | **X**        | **Y**    | **Z** | **W**  |

---

## Critical Issues (Must Fix)

### From Comment Resolution Checker

[Unaddressed code change requests, suspiciously resolved threads]

### From Silent Failure Hunter

[Critical findings with 90%+ confidence]

### From Test Analyzer

[Priority 9-10 test gaps]

### From Type Analyzer

[Scores <5 on any dimension]

---

## High Priority Issues (Should Fix)

### Error Handling (Silent Failure Hunter)

[80-89% confidence findings]

### Test Coverage (Test Analyzer)

[Priority 7-8 gaps]

### Type Design (Type Analyzer)

[Scores 5-6 on dimensions]

### Complexity (Code Simplifier)

[High complexity refactoring suggestions]

---

## Medium Priority (Consider)

[Aggregated medium priority items from all agents]

---

## Positive Observations

[Good patterns found by each agent]

---

## Recommended Action Plan

1. **Immediate:** [Critical issues to fix now]
2. **Before Merge:** [High priority items]
3. **Follow-up:** [Medium priority as separate PRs]

---

## Individual Agent Reports

<details>
<summary>Comment Resolution Checker Full Report</summary>
[Full report from agent]
</details>

<details>
<summary>Silent Failure Hunter Full Report</summary>
[Full report from agent]
</details>

<details>
<summary>Test Analyzer Full Report</summary>
[Full report from agent]
</details>

<details>
<summary>Type Design Analyzer Full Report</summary>
[Full report from agent]
</details>

<details>
<summary>Code Simplifier Full Report</summary>
[Full report from agent]
</details>
```

## Confidence and Priority Alignment

Align findings across agents using this unified scale:

| Unified Level | Comment Resolution                     | Silent Failures   | Test Gaps     | Type Issues  | Complexity       |
| ------------- | -------------------------------------- | ----------------- | ------------- | ------------ | ---------------- |
| 🔴 Critical   | Unaddressed code change requests       | 90%+ confidence   | Priority 9-10 | Any score <5 | Cyclomatic >20   |
| 🟡 High       | Suspiciously resolved (no code change) | 80-89% confidence | Priority 7-8  | Scores 5-6   | Cyclomatic 11-20 |
| 🟠 Medium     | Unanswered questions                   | 70-79% confidence | Priority 5-6  | Scores 6-7   | Cyclomatic 6-10  |
| ⚪ Low        | Open discussions                       | 60-69% confidence | Priority 3-4  | Scores 7-8   | Cyclomatic 1-5   |

## Example Usage

```
User: /comprehensive-review postgres
→ Runs all agents on postgres connector in parallel

User: /comprehensive-review snowflake sequential
→ Runs all agents on snowflake connector sequentially

User: /comprehensive-review --agents=tests,silent-failures
→ Runs only test-analyzer and silent-failure-hunter on changed files
```

## Remember

- **Parallel is faster** but agents can't share context
- **Sequential is thorough** but takes longer
- **Aggregate intelligently** - don't just concatenate reports
- **Prioritize findings** - critical issues first
- **Be actionable** - every finding needs a clear fix
