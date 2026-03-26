# DataHub Setup

Set up your DataHub connection and configure default scopes for the interaction skills.

## What it does

**Phase 1 — Setup:**

1. Checks your environment (Python, CLI, config)
2. Installs the DataHub CLI in a virtual environment
3. Configures GMS URL and authentication
4. Verifies connectivity

**Phase 2 — Configure (optional):**

1. Sets default scopes (platforms, domains, entity types)
2. Creates named configuration profiles
3. Verifies configuration with a test query

## Usage

```
/datahub-setup
/datahub-setup set up DataHub CLI
/datahub-setup focus on Snowflake in the Finance domain
/datahub-setup create a profile for the data-eng team
```
