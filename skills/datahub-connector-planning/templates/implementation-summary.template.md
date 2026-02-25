# {{ source_name }} Connector - Implementation Summary

**Last Updated**: {{ date }}

## Quick Reference

| Item            | Value                                             |
| --------------- | ------------------------------------------------- |
| Source Type     | {{ source_type }}                                 |
| Source Category | {{ source_category }}                             |
| Base Class      | {{ base_class }}                                  |
| Config Class    | {{ config_class }}                                |
| Connector Path  | `src/datahub/ingestion/source/{{ source_name }}/` |

## Files

| File          | Purpose                             |
| ------------- | ----------------------------------- |
| `__init__.py` | Package exports                     |
| `config.py`   | Configuration classes               |
| `source.py`   | Main source implementation          |
| `client.py`   | API client (API/NoSQL sources only) |

## Configuration

### Required Fields

```yaml
source:
  type: { { source_name } }
  config:
    # Required fields here
```

### Optional Fields

```yaml
# Optional fields here
```

## Capabilities

<!-- Fill in the capabilities relevant to the source category.
     See references/source-type-mapping.yml for the expected capabilities per category.
     Common capabilities by source type:
     - SQL: SCHEMA_METADATA, CONTAINERS, LINEAGE_COARSE, LINEAGE_FINE, DATA_PROFILING, USAGE_STATS
     - BI: DASHBOARDS, CHARTS, LINEAGE_COARSE, CONTAINERS, OWNERSHIP, TAGS
     - Orchestration: DATA_FLOW, DATA_JOB, LINEAGE_COARSE, OWNERSHIP, TAGS
     - Streaming: SCHEMA_METADATA, CONTAINERS, LINEAGE_COARSE
     - ML: ML_MODELS, ML_MODEL_GROUPS, CONTAINERS, LINEAGE_COARSE
     - Identity: CORP_USERS, CORP_GROUPS, GROUP_MEMBERSHIP
     - NoSQL: SCHEMA_METADATA, CONTAINERS
-->

| Capability   | Status                        | Notes   |
| ------------ | ----------------------------- | ------- |
| (capability) | Implemented / Not Implemented | (notes) |

## Implementation Notes

### Key Design Decisions

1. Decision and rationale
2. Decision and rationale

### Workarounds

| Issue          | Workaround        |
| -------------- | ----------------- |
| Describe issue | How it was solved |

### Known Limitations

1. Limitation and impact
2. Limitation and impact

## Testing

| Test Type         | Location                                      | Coverage |
| ----------------- | --------------------------------------------- | -------- |
| Unit Tests        | `tests/unit/test_{{ source_name }}_source.py` | XX%      |
| Integration Tests | `tests/integration/{{ source_name }}/`        | N/A      |

## Verification Status

- [ ] Primary entity extraction verified
- [ ] All planned capabilities produce output
- [ ] Container hierarchy verified (if applicable)
- [ ] Lineage verified (if applicable)
- [ ] DataHub UI verification complete
- [ ] Documentation written
