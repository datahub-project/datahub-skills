# datahub-quality-oss-writes

Quality **writes** for open source DataHub — the incident and external-assertion operations that work on self-hosted GMS.

## What it does

- **Incidents:** raise (`raiseIncident`), update, and resolve (`updateIncidentStatus` with `IncidentStatusInput`) incidents via GraphQL — verified working on OSS
- **External assertions:** declare `source: EXTERNAL` assertions (`AssertionInfo` aspect) and report SUCCESS/FAILURE runs (`AssertionRunEvent` timeseries) via the Python SDK, visible in the Validations tab

Cloud-only features (native/smart assertions, monitors, subscriptions) are explicitly out of scope — see `datahub-quality`.

## Usage

```
> Raise an incident on the orders table
> Resolve incident urn:li:incident:... as fixed
> Register my checker's column check as an external assertion on orders
> Report a FAILURE result for that assertion
```

## Files

| File       | Purpose                 |
| ---------- | ----------------------- |
| `SKILL.md` | Main skill instructions |
