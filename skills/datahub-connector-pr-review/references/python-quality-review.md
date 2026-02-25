# Python Code Quality Review Deep Dive

Review code as a Python expert specializing in clean, performant, and idiomatic Python.

**Source of truth for standards:** `${CLAUDE_PLUGIN_ROOT}/standards/code_style.md`

---

## Focus Areas

- **Advanced Python Features**: Decorators, metaclasses, descriptors, context managers
- **Async/Await & Concurrency**: Proper async patterns, thread safety, concurrent programming
- **Performance Optimization**: Profiling, bottleneck identification, memory efficiency
- **Design Patterns & SOLID**: Appropriate patterns, single responsibility, dependency inversion
- **Testing Quality**: pytest usage, mocking, fixtures, edge cases
- **Type Hints & Static Analysis**: mypy compliance, ruff formatting

---

## Python Quality Checklist

**See `${CLAUDE_PLUGIN_ROOT}/standards/code_style.md` for the complete checklist.**

Key areas to verify:

- Formatting and naming conventions
- Data structures (dataclasses/Pydantic vs dicts/tuples)
- Architecture guidelines (inheritance depth, global state)
- Type safety and mypy compliance

---

## Static Analysis Commands

```bash
# Type checking
mypy src/datahub/ingestion/source/<connector>/ --strict

# Linting and formatting
ruff check src/datahub/ingestion/source/<connector>/
ruff format --check src/datahub/ingestion/source/<connector>/

# Complexity analysis
radon cc src/datahub/ingestion/source/<connector>/ -a -s
```

---

## Python Anti-Patterns to Flag

| Anti-Pattern                  | Issue                                            | Fix                              |
| ----------------------------- | ------------------------------------------------ | -------------------------------- |
| Mutable default args          | `def f(x=[])` causes bugs                        | Use `None` and create inside     |
| Bare except                   | Catches everything including `KeyboardInterrupt` | Catch specific exceptions        |
| Using `type()` for comparison | Doesn't handle inheritance                       | Use `isinstance()`               |
| String concatenation in loops | O(n^2) performance                               | Use `join()` or list             |
| Not using context managers    | Resource leaks                                   | Use `with` statements            |
| Global mutable state          | Hard to test, thread-unsafe                      | Dependency injection             |
| Deep nesting                  | Hard to read/maintain                            | Early returns, extract functions |
| God classes                   | Too many responsibilities                        | Split into focused classes       |

---

## Python Review Output

When reporting Python quality findings:

- Cite specific PEP references where applicable
- Provide before/after code examples
- Include performance impact if relevant
- Suggest refactoring with concrete examples
