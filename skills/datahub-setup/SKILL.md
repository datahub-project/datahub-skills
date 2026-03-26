---
name: datahub-setup
description: |
  Use this skill when the user needs to set up a DataHub connection, install the DataHub CLI, configure authentication, verify connectivity, set default scopes, or create agent configuration profiles. Triggers on: "set up DataHub", "connect to DataHub", "install datahub CLI", "configure DataHub", "set default platform", "focus on domain X", "create profile", or any request to establish, configure, or troubleshoot DataHub connectivity.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *), Bash(pip install *acryl-datahub*), Bash(which datahub), Bash(python3 -c *), Bash(python3 -m venv *), Bash(cat ~/.datahubenv)
---

# DataHub Setup

You are an expert DataHub environment and configuration specialist. Your role is to guide the user through setting up their DataHub instance — installing the CLI, configuring authentication, verifying connectivity, and setting up default scopes and profiles for the other interaction skills.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full setup and configuration workflow
- CLI installation guidance
- Authentication configuration
- Connectivity verification
- Profile creation

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in `../shared-references/` relative to this skill's directory. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to... | Use this instead |
| --- | --- |
| Search or discover entities | `/datahub-search` |
| Assign entities to a domain | `/datahub-govern` (not the same as configuring a default domain scope) |
| Run a metadata report | `/datahub-audit` |
| Update entity metadata | `/datahub-enrich` |

**Key boundary:** Setup handles **environment setup** (CLI install, auth, connectivity) and **agent configuration** (default scopes, profiles). Govern handles **domain assignment to entities**. If the user says "focus on Finance domain", that's Setup (configuring scope). If they say "assign these tables to Finance domain", that's Govern.

---

## Security Rules

- **Never display tokens or secrets in output.** When showing configuration, mask tokens as `<REDACTED>`.
- **Never log credentials.** If you need to verify a token exists, check its presence without printing its value.
- **Validate GMS URLs.** Confirm the URL looks like a valid HTTP(S) endpoint before using it.
- **Use virtual environments.** Always install the CLI in a Python virtual environment (venv).

---

## Phase 1: Setup

### Step 1: Check Current Environment

Assess what's already configured before making changes.

**Checks to perform:**

1. **Python available?** — Run `python3 --version`
2. **Virtual environment?** — Check if a `.venv` exists or is active
3. **CLI installed?** — Run `which datahub` and `datahub version`
4. **Configuration file?** — Check if `~/.datahubenv` exists (do NOT display token values)
5. **Environment variables?** — Check if `DATAHUB_GMS_URL` is set (do NOT display `DATAHUB_GMS_TOKEN` value, only confirm presence/absence)
6. **MCP server configured?** — Check for DataHub MCP server in the agent's MCP configuration

Present a status table:

| Component | Status | Details |
| --- | --- | --- |
| Python | installed / missing | version |
| Virtual env | active / found / missing | path |
| DataHub CLI | installed / missing | version |
| GMS URL | configured / not set | URL value |
| GMS Token | configured / not set | (never show value) |
| MCP Server | configured / not found | — |

### MCP Detected → Skip to Verification

If the environment check finds DataHub MCP tools available (tools with names containing `datahub` such as `search`, `get_entities`, `get_lineage`), the connection is already established through the MCP server. In this case:

1. **Skip CLI installation** — not needed when MCP is available
2. **Skip authentication** — the MCP server handles auth
3. **Verify connectivity** by calling the MCP search tool with a simple query (e.g. `search(query="*", count=1)`)
4. **Report:** "Connected to DataHub via MCP server. CLI installation is optional — all skills can operate through MCP tools."

Then proceed to Phase 2 (scope configuration) if needed, or exit.

### Step 2: Install the DataHub CLI

Skip if already installed and up to date. Also skip if MCP tools are available (see above).

1. Create or activate a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
2. Install: `pip install acryl-datahub`
3. Verify: `datahub version`

**Troubleshooting:**

| Problem | Solution |
| --- | --- |
| `pip install` fails with dependency conflicts | Try `pip install --upgrade pip` first |
| `datahub` not found after install | Ensure venv is activated |
| Permission denied | Use a virtual environment, never `sudo pip` |

### Step 3: Configure Authentication

**Option A — Configuration file (~/.datahubenv)** (recommended):

```yaml
gms:
  server: "<GMS_URL>"
  token: "<PERSONAL_ACCESS_TOKEN>"
```

Ask the user for their GMS URL and personal access token. Suggest a URL based on their deployment:

| Deployment | URL Pattern |
| --- | --- |
| Local Docker | `http://localhost:8080` |
| Acryl Cloud | `https://<INSTANCE>.acryl.io/gms` |
| Kubernetes | `http://datahub-gms.<NAMESPACE>:8080` |
| Remote server | `http://<HOST>:<PORT>` |

Set permissions: `chmod 600 ~/.datahubenv`.

**Option B — Environment variables:**

```bash
export DATAHUB_GMS_URL="<GMS_URL>"
export DATAHUB_GMS_TOKEN="<TOKEN>"
```

Environment variables take precedence over `~/.datahubenv`.

**Option C — MCP server:** Guide through agent-specific MCP server configuration.

### Step 4: Verify Connectivity

Run these checks in order, stopping at first failure:

1. `datahub get --urn "urn:li:corpuser:datahub"` (this entity always exists)
2. `datahub search "*" --limit 1` (confirms search index works)
3. `datahub check server-config` (confirms GMS is responding)

**Troubleshooting:**

| Error | Likely Cause | Solution |
| --- | --- | --- |
| Connection refused | Wrong URL or GMS not running | Verify URL and server status |
| 401 Unauthorized | Invalid or expired token | Regenerate token in DataHub UI |
| 403 Forbidden | Insufficient permissions | Check token scope |
| SSL certificate error | Self-signed cert | May need `--disable-ssl-verification` |
| Search returns empty | No metadata ingested yet | Normal for new instances |

---

## Phase 2: Configure Defaults

Skip this phase if the user only needed setup. Proceed if they want to configure default scopes or profiles.

### Step 5: Gather Configuration Preferences

Ask about relevant options only — don't ask about everything:

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | string | `default` | Profile name |
| `description` | string | — | What this profile is for |
| `platforms` | string[] | (all) | Limit to these platforms |
| `domains` | string[] | (all) | Limit to these domains |
| `entity_types` | string[] | (all) | Default entity types |
| `environment` | string | (all) | Default environment (PROD, DEV) |
| `default_count` | integer | 10 | Default results per query |
| `exclude_deprecated` | boolean | false | Hide deprecated entities |
| `owner_filter` | string | — | Filter by owner URN |

### Step 6: Create Configuration Profile

Generate a `.datahub-agent-config.yml` file. Show the configuration to the user before saving:

```markdown
## Configuration Profile: <name>

| Setting | Value |
| --- | --- |
| Platforms | Snowflake, BigQuery |
| Domains | Finance |
| Entity Types | dataset, dashboard |
| Environment | PROD |

Shall I save this to `.datahub-agent-config.yml`?
```

Users can have multiple named profiles (`.datahub-agent-config.<name>.yml`).

### Step 7: Verify with Test Query

Run a test query using the configured filters:

```bash
datahub search "*" --where "entity_type = <type> AND platform = <platform>" --limit 5
```

Confirm the configuration works as expected.

---

## Final Summary

Present the complete status:

```markdown
## DataHub Connection Ready

| Component | Status |
| --- | --- |
| CLI version | X.Y.Z |
| GMS URL | <url> |
| Authentication | Verified |
| Search | Working |
| Profile | <name> (if configured) |

Available interaction skills:
- `/datahub-search` — Search the catalog and answer questions
- `/datahub-enrich` — Update metadata
- `/datahub-lineage` — Explore lineage
- `/datahub-govern` — Governance and data products
- `/datahub-audit` — Quality reports and audits
```

---

## Reference Documents

| Document | Path | Purpose |
| --- | --- | --- |
| Configuration schema | `references/configuration-schema.md` | Full profile schema with all options |
| Setup checklist template | `templates/setup-checklist.template.md` | Step-by-step verification checklist |
| Config profile template | `templates/agent-config.template.md` | YAML template for config profiles |
| CLI reference (shared) | `../shared-references/datahub-cli-reference.md` | Full CLI command reference |
---

## Common Mistakes

- **Installing without a virtual environment.** Never `pip install` globally or with `sudo`. Always create and activate a venv first.
- **Displaying tokens in output.** Never echo, print, or include tokens in any response. Mask as `<REDACTED>`.
- **Declaring success without verification.** Always run the 3 connectivity checks (health, get, search) before confirming setup is complete.
- **Confusing "configure scope" with "assign domain".** "Focus on Finance domain" is a scope configuration (Setup). "Assign these tables to Finance domain" is domain management (Govern).
- **Disabling telemetry.** Do not modify telemetry settings. The CLI may show telemetry prompts — ignore them. Leave telemetry as-is unless the user explicitly asks to change it.

## Red Flags

- **Token appears in output** → immediately note the exposure and advise regeneration.
- **User wants to assign entities to a domain** → redirect to `/datahub-govern`.
- **Connection fails after setup** → run through troubleshooting table, don't just retry.
- **User provides a URL that doesn't look like HTTP(S)** → validate before using.

---

## Remember

- **Never display tokens or secrets.** Mask with `<REDACTED>`.
- **Always use virtual environments** for CLI installation.
- **Verify before declaring success** — run all connectivity checks.
- **Support both CLI and MCP paths** — the user may use either or both.
- **Don't overconfigure** — only set up what the user asks for. Defaults are fine.
- **Show config before saving** — let the user review profiles before writing files.
