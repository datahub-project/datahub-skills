# DataHub Governance Evidence Package

> This package summarizes catalog-visible metadata only. It is supporting
> evidence, not an audit, attestation, certification, legal opinion, or
> compliance determination.

## Collection record

| Field                  | Value                                       |
| ---------------------- | ------------------------------------------- |
| Collected at           | `<ISO-8601 timestamp>`                      |
| DataHub server/profile | `<non-secret identifier>`                   |
| DataHub version        | `<server and client versions>`              |
| Environment            | `<environment>`                             |
| Entity types           | `<types>`                                   |
| Scope filters          | `<platforms, domains, or other filters>`    |
| Sibling handling       | `<separate or collapsed; explain>`          |
| Lineage boundary       | `<direction and hop depth>`                 |
| Structured Properties  | `<exact qualified names or none>`           |
| Collection method      | `<MCP tool names or official CLI>`          |
| Pagination             | `<page size, pages, termination condition>` |
| Completeness           | `<complete or incomplete>`                  |

## Observation summary

These are catalog-observation counts and percentages, not scores.

| Signal                                 |     Observed | Not observed |       Unable | Selected |
| -------------------------------------- | -----------: | -----------: | -----------: | -------: |
| Ownership                              | `<n> (<p>%)` | `<n> (<p>%)` | `<n> (<p>%)` |    `<n>` |
| Documentation                          | `<n> (<p>%)` | `<n> (<p>%)` | `<n> (<p>%)` |    `<n>` |
| Domain                                 | `<n> (<p>%)` | `<n> (<p>%)` | `<n> (<p>%)` |    `<n>` |
| Asset classification                   | `<n> (<p>%)` | `<n> (<p>%)` | `<n> (<p>%)` |    `<n>` |
| Field classification                   | `<n> (<p>%)` | `<n> (<p>%)` | `<n> (<p>%)` |    `<n>` |
| Lineage (`<direction>`, `<hops>` hop)  | `<n> (<p>%)` | `<n> (<p>%)` | `<n> (<p>%)` |    `<n>` |
| `<structured-property-qualified-name>` | `<n> (<p>%)` | `<n> (<p>%)` | `<n> (<p>%)` |    `<n>` |

## Named gaps and unknowns

| Signal     | Not observed on           | Unable to determine on    |
| ---------- | ------------------------- | ------------------------- |
| `<signal>` | `<names plus exact URNs>` | `<names plus exact URNs>` |

## Asset-level evidence

Include every selected asset. Add rows when source surfaces differ.

| Asset    | URN     | Signal     | State                                              | Source surface          | Supporting metadata                                     |
| -------- | ------- | ---------- | -------------------------------------------------- | ----------------------- | ------------------------------------------------------- |
| `<name>` | `<URN>` | `<signal>` | `<Observed, Not observed, or Unable to determine>` | `<aspect or operation>` | `<safe identifier or concise metadata; never row data>` |

## Framework evidence alignment (optional)

This section is a project-authored navigation aid. It does not reproduce
authoritative framework text or determine satisfaction of an objective.

| Framework     | Objective      | Review focus       | Signals and source surfaces   | Counts and exact populations                         | Evidence relevance       | Limitations                   | Source            |
| ------------- | -------------- | ------------------ | ----------------------------- | ---------------------------------------------------- | ------------------------ | ----------------------------- | ----------------- |
| `<framework>` | `<identifier>` | `<original label>` | `<signals; DataHub surfaces>` | `<per-signal observed / not observed / unable URNs>` | `<original explanation>` | `<objective-specific limits>` | `<official link>` |

## Collection errors

- `<operation, asset, safe error summary, affected signal, and completeness effect>`

## Interpretation and limitations

- “Not observed” means the queried catalog signal was absent in the selected
  scope. It does not prove that a real-world process or safeguard is absent.
- `<signal-specific limitation>`

## Human-review follow-ups

| Target URN | Current catalog state | Candidate improvement | Proposed DataHub surface | Approval status |
| ---------- | --------------------- | --------------------- | ------------------------ | --------------- |
| `<URN>`    | `<state>`             | `<proposal>`          | `<surface>`              | `Not requested` |
