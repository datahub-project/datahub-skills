# Platform Registration Guide

## Overview

When adding a new source connector to DataHub, you need to properly register the platform so it appears correctly in the DataHub UI with proper branding, icons, and metadata.

## What Needs to Be in the Codebase

### 1. Platform Definition (Java - metadata-models)

**File**: `metadata-models/src/main/pegasus/com/linkedin/common/DataPlatform.pdl`

Add your platform to the `DataPlatform` enum:

```java
enum DataPlatform {
  // ... existing platforms

  /**
   * Apache Flink
   */
  FLINK
}
```

**Why needed**: This defines the platform as a first-class entity in DataHub's data model.

### 2. Platform Info Configuration (YAML)

**File**: `metadata-service/configuration/src/main/resources/bootstrap_mcps/data-platforms.yaml`

Add platform metadata:

```yaml
- entityUrn: urn:li:dataPlatform:flink
  entityType: dataPlatform
  aspectName: dataPlatformInfo
  changeType: UPSERT
  aspect:
    datasetNameDelimiter: "."
    name: flink
    displayName: Flink
    type: OTHERS
    logoUrl: "assets/platforms/flinklogo.png"
```

### 3. Platform Logo (Static Asset)

**File**: `datahub-web-react/src/images/flinklogo.png`

**Requirements**:

- Format: PNG with transparent background
- Size: Recommended 128x128 pixels minimum, square aspect ratio
- Background: Must be transparent (no white/colored background)
- Style: Simple, recognizable logo that works at small sizes
- Color: Use official brand colors if available

**Why transparent background**: Icons are displayed on various UI backgrounds (light/dark themes, cards, lists). Transparent background ensures they look good everywhere.

**How to create/find**:

1. Check official project website for logo assets
2. Use Vector graphics (SVG) source when available, convert to PNG
3. Use tools like Photoshop, GIMP, or online converters to remove background
4. Test on both light and dark backgrounds

## Alternative: CLI-Based Platform Registration

If you **cannot modify the codebase** (e.g., testing a connector before upstream contribution), you can add platforms via CLI:

### Register Platform via CLI

**Use the dedicated `datahub put platform` command** (recommended):

```bash
# Register Flink platform with logo
datahub put platform \
  --name flink \
  --display_name "Apache Flink" \
  --logo "https://flink.apache.org/img/logo/png/200/flink_squirrel_200_color.png"
```

**Command options**:

- `--name`: Platform identifier (lowercase, used in URNs) - **REQUIRED**
- `--display_name`: Human-readable name shown in UI
- `--logo`: Logo URL that must be reachable from DataHub UI - **REQUIRED**
- `--run-id`: Optional run ID for tracking

**Logo URL requirements**:

- Must be a publicly accessible HTTP/HTTPS URL
- Should point directly to PNG image file
- Image must be accessible from browser (CORS-compatible)
- For local testing, you can use official project URLs (e.g., from Apache website)

**Example with local development**:

```bash
# For Flink using official Apache logo
datahub put platform \
  --name flink \
  --display_name "Flink" \
  --logo "https://flink.apache.org/img/logo/png/200/flink_squirrel_200_color.png"

# Verify registration
datahub get urn --urn "urn:li:dataPlatform:flink" -a dataPlatformInfo
```

**Other platform examples**:

```bash
# Trino
datahub put platform \
  --name trino \
  --display_name "Trino" \
  --logo "https://trino.io/assets/images/logo/trino-og.png"

# DuckDB
datahub put platform \
  --name duckdb \
  --display_name "DuckDB" \
  --logo "https://duckdb.org/images/DuckDB_Logo.png"
```

**Limitations of CLI approach**:

- Logo won't display unless you also upload it to DataHub's static assets - _use link to a http resource in such case_
- Platform won't appear in some dropdown menus
- Not persisted if DataHub is reset
- Recommended only for testing/development

## Complete Platform Registration Checklist

Before considering platform registration complete:

- [ ] Platform info added to `data-platforms.yaml`
- [ ] Logo placed in `datahub-web-react/public/assets/platforms/`
- [ ] Verified platform appears in platform dropdowns

## Testing Platform Registration

After registration, verify:

1. **Logo displays in search results**:
   - Search for datasets from your platform
   - Check that logo appears next to results

2. **Logo displays on entity pages**:
   - Open a dataset from your platform
   - Check logo appears in the header

3. **Platform appears in filters**:
   - Go to search page
   - Check platform appears in "Platform" filter dropdown

## Finding Official Platform Logos

**Best sources for logos**:

1. Official project website (usually in "Press Kit" or "Brand Assets" section)
2. Project's GitHub repository (`docs/`, `assets/`, `static/` folders)
3. Apache Software Foundation press kit (for Apache projects)
4. Wikipedia/Wikimedia Commons (check licensing)
5. Company's brand guidelines page

**License considerations**:

- Verify you have rights to use the logo
- Most open-source projects allow logo use for attribution
- Check project's trademark policy
- Some logos require attribution or have usage restrictions

## Integration with Connector Development

When developing a new connector:

1. **During planning phase**: Identify official logo source
2. **During implementation**: Download and prepare logo
3. **Before documentation**: Register platform (codebase or CLI)
4. **During testing**: Verify logo appears correctly
5. **Before PR**: Ensure all platform registration files are included

Platform registration should be completed **before** the connector PR is merged, so users see proper branding immediately.
