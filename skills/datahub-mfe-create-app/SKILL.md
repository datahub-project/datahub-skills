---
name: datahub-mfe-create-app
description: >-
  Scaffold a new DataHub Micro Frontend (MFE) app with all boilerplate files.
  Use when the user wants to create a new micro frontend, MFE, remote app,
  or Module Federation app for DataHub.
---

# Create a DataHub MFE App

Scaffolds a complete, working Micro Frontend app that integrates with DataHub
via Webpack Module Federation. Generates all 7 required files and guides the
user through building and verifying.

## Step 1: Gather Information

Use the **AskQuestion** tool to collect the following in a single call.

| Question | ID | Options |
|---|---|---|
| App name (kebab-case, e.g. `team-dashboard`) | `app_name` | `test-app` / `N/A - I'll fill it in later` |
| Brief description of what the app does | `app_desc` | `test-description` / `N/A - I'll fill it in later` |
| Dev server port | `port` | `3002` / `3003` / `3004` / `3005` / `3006` |
| Does the app need to call the DataHub GraphQL API? | `needs_graphql` | `Yes` / `No` |

For `app_name` and `app_desc`, present only the `N/A - I'll fill it in later`
option — do NOT suggest values from the workspace. The user will type their own.

### Deriving names from `app_name`

Given an `app_name` like `team-dashboard`:

- **Directory**: `team-dashboard-mfe/` (append `-mfe` if not already present)
- **Module Federation name** (`MF_NAME`): convert to camelCase and append `MFE` — `teamDashboardMFE`
- **Package name**: same as directory name, e.g. `team-dashboard-mfe`
- **Display label**: title-case the words, e.g. `Team Dashboard`

## Step 2: Generate Files

Create the directory at the workspace root (sibling to `datahub-web-react/`).
Generate **all 7 files** using the templates in [templates.md](assets/templates.md).

Apply these substitutions to every template:

| Placeholder | Value |
|---|---|
| `__APP_DIR__` | Directory name |
| `__PACKAGE_NAME__` | Package name |
| `__APP_DESCRIPTION__` | User's description |
| `__PORT__` | Dev server port |
| `__MF_NAME__` | Module Federation name (camelCase + MFE) |
| `__DISPLAY_LABEL__` | Title-cased label |
| `__PUBLIC_PATH_DEV__` | `http://localhost:<PORT>/` |

If `needs_graphql` is **Yes**, include the GraphQL proxy block in `webpack.config.js`
(marked with `{{GRAPHQL_PROXY}}` in the template). If **No**, omit it entirely.

### Files to generate

1. `package.json`
2. `webpack.config.js`
3. `src/mount.tsx`
4. `src/index.tsx`
5. `src/App.tsx`
6. `tsconfig.json`
7. `public/index.html`

## Step 3: Install and Start

**First `cd` into the app directory** — webpack must be started from within it,
not from the workspace root.

```bash
cd __APP_DIR__
npm install
npm start
```

Wait for webpack to compile. The dev server should start on the configured port.

## Step 4: Verify

1. Open `http://localhost:<PORT>/remoteEntry.js` in a browser or curl it.
   It should return JavaScript (not a 404 or HTML error page).
2. Open `http://localhost:<PORT>/` — the standalone dev page should render.

If either check fails, review the webpack output for errors and fix before
proceeding.

## Step 5: Next Steps

Tell the user:

> Your MFE app is running! To integrate it with DataHub, use the
> **datahub-mfe-configure-app** skill — it will walk you through adding this app
> to the DataHub frontend config so it appears at `/mfe/<path>` and optionally
> in the nav sidebar.

Provide a summary of what was created:

```
Created __APP_DIR__/ with 7 files:
  package.json          — dependencies and scripts
  webpack.config.js     — Module Federation + dev server
  src/mount.tsx         — mount() contract for DataHub
  src/index.tsx         — standalone dev entry point
  src/App.tsx           — starter React component
  tsconfig.json         — TypeScript config
  public/index.html     — dev HTML shell

Module Federation name: __MF_NAME__   ← use this as "MFE app name" in datahub-mfe-configure-app
Remote entry URL:       http://localhost:__PORT__/remoteEntry.js
Module path:            __MF_NAME__/mount
```
