# datahub-incident-response

Reusable [DataHub Skill](https://github.com/datahub-project/datahub-skills) for automated
data incident response — detect, root-cause, assess ML blast radius, fix, and write back
postmortems via the metadata graph.

Originated from [Kavach](https://github.com/doPrashams/kavach) (DataHub Agent Hackathon).

## Install

### Claude Code plugin

```bash
# From a fork of datahub-project/datahub-skills with this skill copied under skills/
/plugin install datahub-skills@datahub-skills
```

### Manual

Copy this directory into your fork of `datahub-skills`:

```
skills/datahub-incident-response/
```

Then invoke with `/datahub-incident-response` or let the agent auto-trigger on incident language.

## Usage

1. Ensure DataHub CLI + MCP are configured (`/datahub-setup`).
2. Describe the symptom: failing assertion, null spike, schema drift, etc.
3. The skill walks lineage, query history, ML blast radius, fix plan, and write-back steps.

## Worked examples

See [`examples/`](examples/) — each references real judge-facing artifacts in the repo root
[`examples/`](../../examples/) directory.

## Upstream contribution

Human steps to open the PR: [`docs/handoffs/H10-skill-pr/SUBMIT.md`](../../docs/handoffs/H10-skill-pr/SUBMIT.md).
