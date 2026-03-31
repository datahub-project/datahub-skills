# MFE Configuration Reference

Detailed reference material for the `datahub-mfe-configure-app` skill.

---

## YAML Config Schema

The config file is served by the DataHub Play backend at `/mfe/config`. The
frontend parses it as YAML and validates each entry.

```yaml
subNavigationMode: false    # true = dropdown menu, false = sidebar group
microFrontends:
  - id: unique-id           # Unique identifier (string, required)
    label: Display Name     # Shown in nav and page header (string, required)
    path: /url-path         # URL path — becomes /mfe/url-path (string, must start with /)
    remoteEntry: http://host:port/remoteEntry.js  # Full URL to remote entry (string, required)
    module: federationName/mount   # Must match ModuleFederationPlugin.name + "/mount" (string with /)
    flags:
      enabled: true         # Whether to load this MFE (boolean, required)
      showInNav: true       # Whether to show in sidebar (boolean, required)
    navIcon: Trophy         # Phosphor icon name (non-empty string, required)
```

### Validation Rules (from `mfeConfigLoader.tsx`)

- `id`: must be a string
- `label`: must be a string
- `path`: must be a string starting with `/`
- `remoteEntry`: must be a string
- `module`: must be a string containing `/` (pattern: `moduleName/functionName`)
- `flags`: must be an object with boolean `enabled` and `showInNav`
- `navIcon`: must be a non-empty string

Invalid entries are logged and skipped; they don't break other MFEs.

---

## Environment Variables

| Variable | Where | Purpose |
|---|---|---|
| `MFE_CONFIG_FILE_PATH` | `datahub-frontend` container (Docker, k8s) | Absolute path to the MFE YAML config file |
| `MFE_PUBLIC_PATH` | MFE build time | Sets webpack `output.publicPath` for production builds |

### Default values by workflow

| Workflow | Config file used | How the default is set |
|---|---|---|
| Docker / `datahub-dev.sh` | `datahub-frontend/conf/mfe.config.dev.yaml` | `ENV MFE_CONFIG_FILE_PATH=...` in `docker/datahub-frontend/Dockerfile` line 58 |
| Play server / sbt / IntelliJ | `datahub-frontend/conf/mfe.config.local.yaml` | `MFE_CONFIG_FILE_PATH=../conf/mfe.config.local.yaml` in `datahub-frontend/run/frontend.env` |

**Always edit `mfe.config.dev.yaml` for Docker-based local dev** (the standard
`datahub-dev.sh start` workflow). Changes to `mfe.config.local.yaml` have no
effect unless you're running the Play server directly outside Docker.

---

## Kubernetes Deployment

### ConfigMap for the YAML config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: datahub-mfe-config
  namespace: datahub
data:
  mfe.config.yaml: |
    subNavigationMode: false
    microFrontends:
      - id: my-app
        label: My App
        path: /my-app
        remoteEntry: https://cdn.example.com/my-app/remoteEntry.js
        module: myAppMFE/mount
        flags:
          enabled: true
          showInNav: true
        navIcon: Rocket
```

### Volume mount on `datahub-frontend-react`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datahub-frontend-react
spec:
  template:
    spec:
      containers:
        - name: datahub-frontend-react
          env:
            - name: MFE_CONFIG_FILE_PATH
              value: /mfeconfig/mfe.config.yaml
          volumeMounts:
            - name: mfe-config
              mountPath: /mfeconfig
              readOnly: true
      volumes:
        - name: mfe-config
          configMap:
            name: datahub-mfe-config
```

### Helm values (if using the DataHub Helm chart)

```yaml
datahub-frontend:
  extraEnvs:
    - name: MFE_CONFIG_FILE_PATH
      value: /mfeconfig/mfe.config.yaml
  extraVolumeMounts:
    - name: mfe-config
      mountPath: /mfeconfig
      readOnly: true
  extraVolumes:
    - name: mfe-config
      configMap:
        name: datahub-mfe-config
```

---

## Production `remoteEntry.js` Hosting

The `remoteEntry.js` bundle and its chunks need to be accessible from the
user's browser. Common hosting options:

| Method | URL pattern | Notes |
|---|---|---|
| CDN (S3 + CloudFront) | `https://cdn.example.com/my-mfe/remoteEntry.js` | Best performance, set `MFE_PUBLIC_PATH` during build |
| Static file server (nginx) | `https://mfe.internal.company.com/my-mfe/remoteEntry.js` | Simple, good for internal tools |
| Same k8s cluster (Service) | `http://my-mfe-service:3002/remoteEntry.js` | Only works if browser can reach the service |

Set `MFE_PUBLIC_PATH` so webpack writes correct chunk URLs:

```bash
MFE_PUBLIC_PATH=https://cdn.example.com/my-mfe/ npm run build
```

---

## Module Name Matching

The `module` field in the YAML config MUST exactly match the
`ModuleFederationPlugin.name` in the MFE's webpack config.

```
YAML config:     module: teamDashboardMFE/mount
                          ^^^^^^^^^^^^^^^^^
Webpack config:  new ModuleFederationPlugin({ name: 'teamDashboardMFE', ... })
                                                     ^^^^^^^^^^^^^^^^^
```

If these don't match, the MFE will fail to load with a "Container not found"
or "Module not found" error in the browser console.

---

## Troubleshooting

### MFE doesn't load — blank page at `/mfe/<path>`

1. **Check browser console** for errors. Common messages:
   - `ScriptExternalLoadError` — `remoteEntry.js` URL is unreachable
   - `Module ./mount does not exist in container` — module name mismatch
   - `Shared module react is not available` — React version conflict

2. **Verify `remoteEntry.js` is accessible**: Open the URL directly in the
   browser. It should return JavaScript. If you get CORS errors, ensure the
   MFE dev server sets `Access-Control-Allow-Origin: *` headers.

3. **Verify module name**: The `module` field in YAML must be
   `<ModuleFederationPlugin.name>/mount`.

### CORS errors in browser console

The MFE dev server must include these headers:

```js
headers: {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
    'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization',
},
```

These are included by default in the `datahub-mfe-create-app` scaffold.

### Nav item doesn't appear

- Verify `flags.showInNav: true` in the YAML config.
- Verify `flags.enabled: true`.
- Verify the `navIcon` value is a valid Phosphor icon name (case-sensitive).
- Restart the frontend after config changes.

### Config not loading (404 on `/mfe/config`)

- **Docker / datahub-dev.sh**: Edit `datahub-frontend/conf/mfe.config.dev.yaml`
  and run `scripts/dev/datahub-dev.sh rebuild --wait`. The file is baked into
  the image — a restart alone is not enough.
- **Play server**: Ensure `MFE_CONFIG_FILE_PATH` in `datahub-frontend/run/frontend.env`
  points to `mfe.config.local.yaml` and that you've restarted the server.
- **k8s**: Ensure `MFE_CONFIG_FILE_PATH` env var is set and the ConfigMap
  volume is mounted at the expected path. Restart the pod after changes.

### MFE loads but styles look wrong

MFEs run inside the DataHub page and inherit some global styles. Use scoped
styles (CSS modules, styled-components, or inline styles) to avoid conflicts
with DataHub's Ant Design styles.

### Production build works locally but not in k8s

Check that `MFE_PUBLIC_PATH` was set correctly during the production build.
Without it, webpack defaults to `auto` which may resolve to the wrong base URL
in some hosting setups.
