---
name: datahub-mfe-configure-app
description: >-
  Configure a DataHub instance to load and display a Micro Frontend (MFE) app.
  Use when the user wants to register an MFE with DataHub, add an MFE to the
  nav sidebar, set up MFE config for local dev or production/k8s, or
  troubleshoot MFE loading issues.
---

# Configure an MFE in DataHub

Walks through registering a Micro Frontend app with the DataHub frontend so it
loads at `/mfe/<path>` and optionally appears in the navigation sidebar. Covers
local development, production/k8s deployment, and troubleshooting.

## Step 1: Gather Information

Use the **AskQuestion** tool to collect the following in a single call.

| Question | ID | Options |
|---|---|---|
| Are you configuring for local development or production/k8s? | `env_target` | `Local development` / `Production / Kubernetes` |
| MFE app name — the `name` field inside `new ModuleFederationPlugin({ name: '...' })` in the MFE's `webpack.config.js`. **Must match exactly.** | `mf_name` | `testAppMFE` / `N/A - I'll fill it in later` |
| URL path where the MFE should be accessible, e.g. `/dashboard` (must start with `/`) | `mfe_path` | `/test_page` / `N/A - I'll fill it in later` |
| `remoteEntry.js` URL, e.g. `http://localhost:3002/remoteEntry.js` | `remote_entry_url` | `http://localhost:3002/remoteEntry.js` / `N/A - I'll fill it in later` |
| Display label for navigation, e.g. `Team Dashboard` | `display_label` | `Test Dashboard` / `N/A - I'll fill it in later` |
| Should the MFE appear in the left nav sidebar? | `show_in_nav` | `Yes` / `No` |
| Nav icon | `nav_icon` | `ChartBar` / `Trophy` / `Gear` / `HandWaving` / `Lightning` / `MagnifyingGlass` / `Database` / `Users` / `Shield` / `Bell` / `Flag` / `Star` / `Heart` / `Cube` / `Table` / `Code` / `Globe` / `Rocket` |

If `env_target` is **Local development**, ask one follow-up question using
**AskQuestion** before proceeding:

| Question | ID | Options |
|---|---|---|
| How are you running DataHub locally? | `local_mode` | `Docker / datahub-dev.sh (standard)` / `Play server directly (sbt / IntelliJ)` |

For the `N/A - I'll fill it in later` fields (`mf_name`, `mfe_path`,
`remote_entry_url`, `display_label`), do NOT invent or suggest values from the
workspace. The user will type their own.

> **Finding the MFE app name**: Open the MFE's `webpack.config.js` and look for
> the `ModuleFederationPlugin` block. The `name` property is what goes here:
> ```js
> new ModuleFederationPlugin({ name: 'teamDashboardMFE', ... })
> //                                   ^^^^^^^^^^^^^^^^^  ← this value
> ```
> If the name in the YAML config doesn't match this exactly, the MFE will
> fail to load. If you used the `datahub-mfe-create-app` skill, the name was printed
> in the summary as "Module Federation name".

## Step 2: Generate the YAML Config Entry

Build the config entry from the gathered values:

```yaml
  - id: __MFE_ID__
    label: __DISPLAY_LABEL__
    path: __MFE_PATH__
    remoteEntry: __REMOTE_ENTRY_URL__
    module: __MF_NAME__/mount
    flags:
      enabled: true
      showInNav: __SHOW_IN_NAV__
    navIcon: __NAV_ICON__
```

Where `__MFE_ID__` is derived from the path (strip leading `/`, replace `/`
with `-`), e.g. path `/dashboard` becomes id `dashboard`.

## Step 3: Apply the Configuration

### Local Development — Docker / `datahub-dev.sh` (standard)

The Docker image has `MFE_CONFIG_FILE_PATH` baked in at build time pointing to
`/datahub-frontend/conf/mfe.config.dev.yaml` (set in `docker/datahub-frontend/Dockerfile`).
**This is the file to edit for any Docker-based workflow.**

1. Read the current `datahub-frontend/conf/mfe.config.dev.yaml`.
2. Append the new entry under `microFrontends:`. If the file is empty, use:

```yaml
subNavigationMode: false
microFrontends:
  - id: ...
    ...
```

3. Rebuild the frontend container so the updated file is baked into the image:

```bash
scripts/dev/datahub-dev.sh rebuild --wait
```

### Local Development — Play server directly (sbt / IntelliJ)

`datahub-frontend/run/frontend.env` points `MFE_CONFIG_FILE_PATH` to
`../conf/mfe.config.local.yaml`. **Edit that file instead.**

1. Read the current `datahub-frontend/conf/mfe.config.local.yaml`.
2. Append the new entry under `microFrontends:`.
3. Restart the Play server — no rebuild needed, the file is read from disk:

```bash
cd datahub-frontend/run && ./run-local-frontend
```

### Production / Kubernetes

Tell the user:

> Since you selected **Production / Kubernetes**, I won't edit any local config
> files — instead here's what you need.

1. Show the user the complete YAML config to add to their production config
   file (which may live in a separate config repo).

2. Explain the env var and volume mount setup. See [reference.md](references/reference.md)
   for the full k8s ConfigMap pattern.

3. Remind the user about `MFE_PUBLIC_PATH`:

> When deploying your MFE to a CDN or static host, set the `MFE_PUBLIC_PATH`
> env var during the MFE's production build so webpack knows the correct
> public URL for chunk loading.
> ```bash
> MFE_PUBLIC_PATH=https://cdn.example.com/my-mfe/ npm run build
> ```

## Step 4: Verify

Guide the user through these checks:

1. **Standalone check**: Open `__REMOTE_ENTRY_URL__` in a browser — should
   return JavaScript content (not 404 or HTML).

2. **Integration check**: Navigate to `http://localhost:9002/mfe__MFE_PATH__`
   (local) or the equivalent production URL. The MFE should render inside the
   DataHub chrome.

3. **Nav check** (if `showInNav: true`): The sidebar should show the
   `__DISPLAY_LABEL__` item with the chosen icon. Click it to navigate.

If any check fails, see the Troubleshooting section in [reference.md](references/reference.md).

## Step 5: Summary

Provide the user with a summary. Show only the config file relevant to their
`env_target` — do not mention local config files if they selected Production.

If **local development**:
```
MFE registered in DataHub:
  Path:            /mfe__MFE_PATH__
  Remote entry:    __REMOTE_ENTRY_URL__
  Module:          __MF_NAME__/mount
  Nav sidebar:     __SHOW_IN_NAV__ (icon: __NAV_ICON__)
  Config file:     datahub-frontend/conf/mfe.config.dev.yaml    (Docker / datahub-dev.sh)
                   datahub-frontend/conf/mfe.config.local.yaml  (Play server / IntelliJ)
```

If **Production / Kubernetes**:
```
MFE registered in DataHub:
  Path:            /mfe__MFE_PATH__
  Remote entry:    __REMOTE_ENTRY_URL__
  Module:          __MF_NAME__/mount
  Nav sidebar:     __SHOW_IN_NAV__ (icon: __NAV_ICON__)
  Config file:     <your production config file>
```
