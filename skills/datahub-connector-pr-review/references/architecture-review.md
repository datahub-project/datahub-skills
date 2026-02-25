# Architecture Review Deep Dive

Comprehensive architecture analysis for DataHub connectors.

---

## Context Gathering

Use the context gathering script for comprehensive information:

```bash
./scripts/gather-connector-context.sh <connector> [datahub_repo_path]
```

Or manual commands if needed:

```bash
# Connector structure
ls -la src/datahub/ingestion/source/<connector>/

# Base class identification
grep -r "class.*Source.*:" src/datahub/ingestion/source/<connector>/*.py
```

---

## Architecture Analysis Framework

### 1. System Structure Assessment

- [ ] Map component hierarchy (source, config, client, models)
- [ ] Identify architectural patterns used
- [ ] Analyze module boundaries and separation of concerns
- [ ] Assess layered design (config -> client -> extraction -> emission)
- [ ] Verify correct base class selection (`standards/main.md`)

### 2. Design Pattern Evaluation

- [ ] Identify implemented patterns (Factory, Strategy, Template Method, etc.)
- [ ] Assess pattern consistency across the connector
- [ ] Detect anti-patterns (God class, circular dependencies, tight coupling)
- [ ] Evaluate pattern effectiveness for the use case
- [ ] Check SDK V2 usage patterns (not V1)

### 3. Dependency Architecture

- [ ] Analyze coupling levels between modules
- [ ] Detect circular dependencies
- [ ] Evaluate dependency injection usage
- [ ] Assess architectural boundaries (source <-> client <-> external API)
- [ ] Review import structure and organization

### 4. Data Flow Analysis

- [ ] Trace metadata flow: source system -> extraction -> transformation -> MCE/MCP
- [ ] Evaluate state management (stateful ingestion patterns)
- [ ] Assess data persistence strategies (caching, checkpointing)
- [ ] Validate transformation patterns (source types -> DataHub types)
- [ ] Review WorkUnit emission patterns

### 5. Scalability & Performance Architecture

- [ ] Analyze scaling capabilities (pagination, batching)
- [ ] Evaluate caching strategies
- [ ] Assess potential bottlenecks (N+1 queries, memory usage)
- [ ] Review resource management (connection pooling, cleanup)
- [ ] Check lazy loading and streaming patterns

### 6. Security Architecture

- [ ] Review trust boundaries (credential handling)
- [ ] Assess authentication patterns
- [ ] Analyze authorization flows
- [ ] Evaluate data protection (no sensitive data in logs/MCEs)
- [ ] Check for injection vulnerabilities

---

## Advanced Architecture Analysis

- **Component Testability**: Can components be unit tested in isolation?
- **Configuration Management**: Are configs properly structured and validated?
- **Error Handling Patterns**: Consistent error handling and reporting?
- **Monitoring Integration**: Proper use of report/context for observability?
- **Extensibility Assessment**: Can the connector be extended without modification?

---

## Architecture Checklist Summary

```
Base Class & SDK:
[ ] Correct base class for source type (SQLAlchemy vs StatefulIngestionSourceBase)
[ ] SDK V2 usage throughout
[ ] Proper inheritance chain

Component Structure:
[ ] Separate config class (not embedded in source)
[ ] Separate client class for external communication (API sources)
[ ] Clear separation: config -> client -> extraction -> emission
[ ] No God classes (single responsibility)

Dependencies:
[ ] No circular dependencies
[ ] Proper import organization
[ ] Minimal coupling between components

Data Flow:
[ ] Clear extraction -> transformation -> emission pipeline
[ ] Proper stateful ingestion (if applicable)
[ ] Efficient WorkUnit generation

Patterns:
[ ] Consistent patterns throughout
[ ] No anti-patterns detected
[ ] Follows DataHub connector conventions
```

---

## Architecture Review Output

When reporting architecture findings, include:

- Component diagram (text-based)
- Identified patterns and anti-patterns
- Dependency analysis results
- Specific improvement recommendations
- Refactoring strategies if needed
