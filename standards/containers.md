# Container Creation Patterns

## Related Guides

- [Main Guide](main.md) - Overview and quick start
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [SQL Sources](sql.md) - For SQL database sources
- [API-Based Sources](api.md) - For REST/GraphQL API sources
- [Common Patterns](patterns.md) - Shared patterns and utilities
- [Testing](testing.md) - Testing strategies

---

## Overview

Containers in DataHub represent hierarchical organizational structures like databases, schemas, projects, folders, and workspaces. This guide covers the correct patterns for creating container entities.

## 🔴 CRITICAL: Two Approved Patterns

There are **TWO correct ways** to create containers in DataHub:

1. **Pattern 1: `gen_containers()` function** (recommended for most sources)
2. **Pattern 2: SDK `Container` class** (alternative, newer pattern)

**❌ DO NOT manually emit container aspects** - this is incorrect and will cause issues.

---

## Pattern 1: Using `gen_containers()` Function (Recommended)

### When to Use This Pattern

- ✅ SQL database sources (databases, schemas)
- ✅ API-based sources with hierarchies
- ✅ File-based sources (folders, buckets)
- ✅ Any source extending `StatefulIngestionSourceBase` or `Source`
- ✅ When you need fine-grained control over container aspects

### Step 1: Define Container Keys

Container keys generate unique GUIDs for containers and establish parent-child relationships.

**File**: `<platform_name>.py` or `<platform_name>_models.py`

```python
from datahub.emitter.mcp_builder import ContainerKey, DatabaseKey, SchemaKey

# Example 1: Custom container keys for API-based source
class ProjectKey(ContainerKey):
    """Container key for projects."""
    project_id: str

class SpaceKey(ProjectKey):
    """Container key for spaces within projects."""
    space_id: str

# Example 2: Using built-in keys for SQL sources
# DatabaseKey - for databases
# SchemaKey - for schemas within databases
# These are already defined in datahub.emitter.mcp_builder
```

**Key characteristics:**

- Inherit from `ContainerKey` or existing subclasses
- Add fields that uniquely identify the container
- Parent-child relationships are established automatically via class hierarchy
- Each key has `platform`, `instance`, and `env` fields inherited from `ContainerKey`

### Step 2: Import `gen_containers`

```python
from datahub.emitter.mcp_builder import gen_containers
from datahub.ingestion.source.common.subtypes import (
    DatasetContainerSubTypes,
    BIContainerSubTypes,
)
```

### Step 3: Create Container Workunits

```python
def _emit_database_container(
    self,
    database: str,
    description: Optional[str] = None,
) -> Iterable[MetadataWorkUnit]:
    """Emit database container."""

    # Create container key
    database_key = DatabaseKey(
        database=database,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    # Generate all container metadata
    yield from gen_containers(
        container_key=database_key,
        name=database,
        sub_types=[DatasetContainerSubTypes.DATABASE],
        description=description,
        external_url=f"https://platform.com/database/{database}",
        # Optional parameters:
        domain_urn=domain_urn,  # If domain is specified
        owner_urn=owner_urn,    # If owner is known
        tags=["production"],     # If tags apply
        extra_properties={"db_type": "postgres"},  # Custom properties
        created=created_timestamp,
        last_modified=modified_timestamp,
    )
```

### Step 4: Create Child Containers with Parent References

```python
def _emit_schema_container(
    self,
    database: str,
    schema: str,
    description: Optional[str] = None,
) -> Iterable[MetadataWorkUnit]:
    """Emit schema container under database."""

    # Create parent database key
    database_key = DatabaseKey(
        database=database,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    # Create schema key (extends DatabaseKey)
    schema_key = SchemaKey(
        database=database,
        db_schema=schema,  # Note: field is aliased as "schema"
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    # Generate schema container with parent reference
    yield from gen_containers(
        container_key=schema_key,
        name=schema,
        sub_types=[DatasetContainerSubTypes.SCHEMA],
        parent_container_key=database_key,  # ✅ Links to parent
        description=description,
    )
```

### Step 5: Link Datasets to Containers

```python
from datahub.emitter.mcp_builder import add_dataset_to_container

def _emit_table(
    self,
    database: str,
    schema: str,
    table: str,
) -> Iterable[MetadataWorkUnit]:
    """Emit table dataset."""

    # Create dataset URN
    dataset_urn = make_dataset_urn_with_platform_instance(
        platform=self.platform,
        name=f"{database}.{schema}.{table}",
        platform_instance=self.config.platform_instance,
        env=self.config.env,
    )

    # ... emit dataset metadata ...

    # Link dataset to schema container
    schema_key = SchemaKey(
        database=database,
        db_schema=schema,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    yield from add_dataset_to_container(
        container_key=schema_key,
        dataset_urn=dataset_urn,
    )
```

### Complete Example: SQL Source with Database → Schema → Table Hierarchy

```python
from typing import Iterable, Optional
from datahub.emitter.mce_builder import make_dataset_urn_with_platform_instance
from datahub.emitter.mcp_builder import (
    DatabaseKey,
    SchemaKey,
    gen_containers,
    add_dataset_to_container,
)
from datahub.ingestion.api.workunit import MetadataWorkUnit
from datahub.ingestion.source.common.subtypes import DatasetContainerSubTypes

def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
    """Extract metadata with proper container hierarchy."""

    for database in self._get_databases():
        # 1. Emit database container
        yield from self._emit_database_container(database)

        for schema in self._get_schemas(database):
            # 2. Emit schema container (child of database)
            yield from self._emit_schema_container(database, schema)

            for table in self._get_tables(database, schema):
                # 3. Emit table dataset
                yield from self._emit_table(database, schema, table)

def _emit_database_container(
    self,
    database: str,
) -> Iterable[MetadataWorkUnit]:
    """Emit database container."""

    database_key = DatabaseKey(
        database=database,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    yield from gen_containers(
        container_key=database_key,
        name=database,
        sub_types=[DatasetContainerSubTypes.DATABASE],
        description=f"Database {database}",
    )

def _emit_schema_container(
    self,
    database: str,
    schema: str,
) -> Iterable[MetadataWorkUnit]:
    """Emit schema container under database."""

    database_key = DatabaseKey(
        database=database,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    schema_key = SchemaKey(
        database=database,
        db_schema=schema,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    yield from gen_containers(
        container_key=schema_key,
        name=schema,
        sub_types=[DatasetContainerSubTypes.SCHEMA],
        parent_container_key=database_key,
    )

def _emit_table(
    self,
    database: str,
    schema: str,
    table: str,
) -> Iterable[MetadataWorkUnit]:
    """Emit table dataset and link to schema container."""

    dataset_urn = make_dataset_urn_with_platform_instance(
        platform=self.platform,
        name=f"{database}.{schema}.{table}",
        platform_instance=self.config.platform_instance,
        env=self.config.env,
    )

    # ... yield dataset properties, schema metadata, etc. ...

    # Link to schema container
    schema_key = SchemaKey(
        database=database,
        db_schema=schema,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    yield from add_dataset_to_container(
        container_key=schema_key,
        dataset_urn=dataset_urn,
    )
```

---

## ⚠️ Critical: Emit Parents Before Children (Topological Order)

**Container parents MUST be emitted before their children.** DataHub's browse path generation (`auto_browse_path_v2`) relies on this ordering. If you emit a child before its parent, the browse path will be incorrect and the UI hierarchy will break.

> **Reference Implementation**: See `tableau/tableau.py` function `emit_project_in_topological_order()` (~line 3667) for a production example of recursive topological emission.

### Pattern: Recursive Topological Emission

For variable-depth hierarchies (nested folders, projects), use recursive emission:

```python
def emit_project_containers(self) -> Iterable[MetadataWorkUnit]:
    """Emit all project containers in topological order."""
    emitted_keys: Set[str] = set()  # Track what we've already emitted

    def emit_in_order(project: Project) -> Iterable[MetadataWorkUnit]:
        project_key = self.gen_project_key(project.id)

        # Skip if already emitted (prevents duplicates)
        if project_key.guid() in emitted_keys:
            return
        emitted_keys.add(project_key.guid())

        # Recursively emit parent FIRST
        if project.parent_id:
            parent = self.get_project(project.parent_id)
            yield from emit_in_order(parent)

        # Now emit this project (parent is guaranteed to exist)
        yield from gen_containers(
            container_key=project_key,
            name=project.name,
            parent_container_key=(
                self.gen_project_key(project.parent_id)
                if project.parent_id else None
            ),
            sub_types=[BIContainerSubTypes.FOLDER],
        )

    # Process all projects
    for project in self.get_all_projects():
        yield from emit_in_order(project)
```

### Simple Rule for get_workunits_internal()

In your main extraction method, always emit containers before the entities they contain:

```python
def get_workunits_internal(self):
    # 1. Root containers first (sites, platforms)
    yield from self.emit_site_container()

    # 2. Nested containers in topological order
    yield from self.emit_project_containers()

    # 3. Then entities that reference those containers
    yield from self.emit_workbooks()
    yield from self.emit_dashboards()
```

---

### Complete Example: API Source with Project → Space → Dashboard Hierarchy

```python
from typing import Iterable
from datahub.emitter.mce_builder import make_dashboard_urn
from datahub.emitter.mcp_builder import ContainerKey, gen_containers
from datahub.ingestion.api.workunit import MetadataWorkUnit
from datahub.ingestion.source.common.subtypes import BIContainerSubTypes
from datahub.metadata.schema_classes import ContainerClass
from datahub.emitter.mcp import MetadataChangeProposalWrapper

# Define container keys
class ProjectKey(ContainerKey):
    """Container key for projects."""
    project_id: str

class SpaceKey(ProjectKey):
    """Container key for spaces within projects."""
    space_id: str

def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
    """Extract metadata with project → space → dashboard hierarchy."""

    for project in self._get_projects():
        # 1. Emit project container
        yield from self._emit_project_container(project)

        for space in self._get_spaces(project.id):
            # 2. Emit space container (child of project)
            yield from self._emit_space_container(project.id, space)

            for dashboard in self._get_dashboards(space.id):
                # 3. Emit dashboard and link to space
                yield from self._emit_dashboard(project.id, space.id, dashboard)

def _emit_project_container(
    self,
    project: Project,
) -> Iterable[MetadataWorkUnit]:
    """Emit project container (top-level)."""

    project_key = ProjectKey(
        project_id=project.id,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    yield from gen_containers(
        container_key=project_key,
        name=project.name,
        sub_types=[BIContainerSubTypes.PROJECT],
        description=project.description,
        external_url=f"https://platform.com/projects/{project.id}",
    )

def _emit_space_container(
    self,
    project_id: str,
    space: Space,
) -> Iterable[MetadataWorkUnit]:
    """Emit space container under project."""

    project_key = ProjectKey(
        project_id=project_id,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    space_key = SpaceKey(
        project_id=project_id,
        space_id=space.id,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    yield from gen_containers(
        container_key=space_key,
        name=space.name,
        sub_types=[BIContainerSubTypes.LOOKER_FOLDER],
        parent_container_key=project_key,
        description=space.description,
    )

def _emit_dashboard(
    self,
    project_id: str,
    space_id: str,
    dashboard: Dashboard,
) -> Iterable[MetadataWorkUnit]:
    """Emit dashboard and link to space container."""

    dashboard_urn = make_dashboard_urn(
        platform=self.platform,
        dashboard_id=dashboard.id,
        platform_instance=self.config.platform_instance,
    )

    # ... yield dashboard properties, charts, etc. ...

    # Link dashboard to space container
    space_key = SpaceKey(
        project_id=project_id,
        space_id=space_id,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    container_urn = space_key.as_urn()

    yield MetadataChangeProposalWrapper(
        entityUrn=dashboard_urn,
        aspect=ContainerClass(container=container_urn),
    ).as_workunit()
```

---

## Pattern 2: Using SDK `Container` Class (Alternative)

### When to Use This Pattern

- ✅ Newer sources that prefer SDK style
- ✅ Sources that need a more object-oriented approach
- ✅ When building entities programmatically
- ✅ When you want automatic parent-child relationship handling

### Implementation

```python
from datahub.emitter.mcp_builder import ContainerKey
from datahub.sdk.container import Container
from datahub.ingestion.api.workunit import MetadataWorkUnit

# Define container key
class ProjectKey(ContainerKey):
    """Container key for projects."""
    project_id: str

def _emit_project_container(
    self,
    project: Project,
) -> Iterable[MetadataWorkUnit]:
    """Emit project container using SDK Container class."""

    project_key = ProjectKey(
        project_id=project.id,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    project_container = Container(
        container_key=project_key,
        display_name=project.name,
        description=project.description,
        subtype="Project",
        external_url=f"https://platform.com/projects/{project.id}",
        # Optional parameters:
        parent_container=None,  # Top-level container
        tags=["production"],
        domain="urn:li:domain:engineering",
        extra_properties={"project_type": "analytics"},
    )

    # Container class handles all aspect emission automatically
    yield from project_container.as_workunits()

def _emit_space_container(
    self,
    project_id: str,
    space: Space,
) -> Iterable[MetadataWorkUnit]:
    """Emit space container under project using SDK Container class."""

    space_key = SpaceKey(
        project_id=project_id,
        space_id=space.id,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    space_container = Container(
        container_key=space_key,
        display_name=space.name,
        description=space.description,
        subtype="Space",
        external_url=f"https://platform.com/spaces/{space.id}",
        # parent_container Auto[ProjectKey] - automatically resolved
    )

    yield from space_container.as_workunits()
```

**Advantages of SDK Container class:**

- Cleaner, more object-oriented API
- Automatic parent-child relationship resolution via key hierarchy
- All aspects handled automatically
- Type-safe with better IDE support

**Disadvantages:**

- Newer pattern (less examples in codebase)
- Less control over individual aspects
- May not support all edge cases yet

---

## ❌ ANTI-PATTERN: Manual Container Aspect Emission (WRONG!)

**DO NOT do this** - manually emitting container aspects is incorrect:

```python
# ❌ WRONG - Don't manually emit ContainerPropertiesClass
from datahub.metadata.schema_classes import ContainerPropertiesClass, ContainerClass

def _emit_organization_container(self, org_id: str):
    org_urn = make_container_urn(guid=org_id)

    # ❌ WRONG - Manually creating ContainerPropertiesClass
    container_properties = ContainerPropertiesClass(
        name=f"Organization ({org_id})",
        description="Organization container",
        customProperties={"org_id": org_id},
    )

    # ❌ WRONG - Manually emitting container properties
    yield MetadataChangeProposalWrapper(
        entityUrn=org_urn,
        aspect=container_properties,
    ).as_workunit()

    # ❌ WRONG - Manually emitting status
    yield MetadataChangeProposalWrapper(
        entityUrn=org_urn,
        aspect=StatusClass(removed=False),
    ).as_workunit()

    # This approach is incorrect because:
    # 1. Missing DataPlatformInstance aspect
    # 2. Missing SubTypes aspect
    # 3. Not using proper container key for GUID generation
    # 4. Manual aspect emission error-prone
    # 5. Doesn't integrate with browse paths v2
```

**✅ CORRECT - Use `gen_containers()` instead:**

```python
from datahub.emitter.mcp_builder import ContainerKey, gen_containers

class OrganizationKey(ContainerKey):
    org_id: str

def _emit_organization_container(self, org_id: str):
    org_key = OrganizationKey(
        org_id=org_id,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    # ✅ CORRECT - Use gen_containers()
    yield from gen_containers(
        container_key=org_key,
        name=f"Organization ({org_id})",
        sub_types=["organization"],
        description="Organization container",
        extra_properties={"org_id": org_id},
    )
```

---

## Built-in Container Keys

DataHub provides several built-in container key classes in `datahub.emitter.mcp_builder`:

```python
from datahub.emitter.mcp_builder import (
    ContainerKey,        # Base class
    DatabaseKey,         # For databases
    SchemaKey,           # For schemas (extends DatabaseKey)
    ProjectIdKey,        # For projects
    CatalogKey,          # For catalogs
    UnitySchemaKey,      # For Unity Catalog schemas
    MetastoreKey,        # For metastores
    BucketKey,           # For S3/GCS buckets
    FolderKey,           # For folders
    BigQueryDatasetKey,  # For BigQuery datasets
    NamespaceKey,        # For Iceberg namespaces
)
```

**Use built-in keys when available** - don't recreate them.

---

## Container Subtypes

Use appropriate subtypes from `datahub.ingestion.source.common.subtypes`:

### Dataset Container Subtypes

```python
from datahub.ingestion.source.common.subtypes import DatasetContainerSubTypes

# Common subtypes:
DatasetContainerSubTypes.DATABASE    # For databases
DatasetContainerSubTypes.SCHEMA      # For schemas
DatasetContainerSubTypes.CATALOG     # For catalogs
DatasetContainerSubTypes.FILESYSTEM  # For file systems
```

### BI Container Subtypes

```python
from datahub.ingestion.source.common.subtypes import BIContainerSubTypes

# Common subtypes:
BIContainerSubTypes.LOOKER_FOLDER    # Generic folder
BIContainerSubTypes.PROJECT          # Projects
BIContainerSubTypes.POWERBI_WORKSPACE  # PowerBI workspace
BIContainerSubTypes.TABLEAU_WORKBOOK   # Tableau workbook
```

### Job Container Subtypes

```python
from datahub.ingestion.source.common.subtypes import JobContainerSubTypes

# Common subtypes:
JobContainerSubTypes.NIFI_PROCESS_GROUP
JobContainerSubTypes.AIRFLOW_DAG
```

---

## Best Practices

### 1. Avoid Duplicate Container Emission

Track processed containers to avoid emitting the same container multiple times:

```python
def __init__(self, config, ctx):
    super().__init__(config, ctx)
    self.processed_containers: Set[str] = set()

def _emit_database_container(self, database: str):
    database_key = DatabaseKey(
        database=database,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

    container_guid = database_key.guid()

    # Check if already processed
    if container_guid in self.processed_containers:
        return

    yield from gen_containers(
        container_key=database_key,
        name=database,
        sub_types=[DatasetContainerSubTypes.DATABASE],
    )

    self.processed_containers.add(container_guid)
```

### 2. Emit Containers Before Datasets

Always emit containers before the datasets they contain:

```python
# ✅ CORRECT - Emit container first
yield from self._emit_schema_container(database, schema)
yield from self._emit_table(database, schema, table)

# ❌ WRONG - Emit dataset before container
yield from self._emit_table(database, schema, table)
yield from self._emit_schema_container(database, schema)
```

### 3. Use Consistent Container Keys

Use the same container key construction everywhere:

```python
# ✅ CORRECT - Consistent key construction
def _make_schema_key(self, database: str, schema: str) -> SchemaKey:
    """Centralized schema key construction."""
    return SchemaKey(
        database=database,
        db_schema=schema,
        platform=self.platform,
        instance=self.config.platform_instance,
        env=self.config.env,
    )

# Use it everywhere
schema_key = self._make_schema_key(database, schema)
yield from gen_containers(container_key=schema_key, ...)
yield from add_dataset_to_container(container_key=schema_key, ...)
```

### 4. Include External URLs When Available

Provide links to the original platform:

```python
yield from gen_containers(
    container_key=database_key,
    name=database,
    sub_types=[DatasetContainerSubTypes.DATABASE],
    external_url=f"https://platform.com/database/{database}",  # ✅ Include URL
)
```

### 5. Add Descriptions and Metadata

Enrich containers with metadata:

```python
yield from gen_containers(
    container_key=database_key,
    name=database,
    sub_types=[DatasetContainerSubTypes.DATABASE],
    description=f"Production database for {database}",
    extra_properties={
        "database_type": "postgres",
        "version": "14.5",
        "size_gb": "1024",
    },
    tags=["production", "pii"],
    owner_urn="urn:li:corpuser:admin",
    created=created_timestamp,
    last_modified=modified_timestamp,
)
```

---

## Testing Container Creation

### Unit Test Example

```python
def test_container_creation():
    """Test container key generation and URN creation."""

    database_key = DatabaseKey(
        database="test_db",
        platform="myplatform",
        instance="prod",
        env="PROD",
    )

    # Test GUID generation
    guid = database_key.guid()
    assert guid == datahub_guid({"database": "test_db", "instance": "prod"})

    # Test URN generation
    urn = database_key.as_urn()
    assert urn == f"urn:li:container:{guid}"

    # Test parent key resolution
    schema_key = SchemaKey(
        database="test_db",
        db_schema="test_schema",
        platform="myplatform",
        instance="prod",
        env="PROD",
    )

    parent_key = schema_key.parent_key()
    assert isinstance(parent_key, DatabaseKey)
    assert parent_key.database == "test_db"
```

### Integration Test Example

```python
def test_container_hierarchy_in_golden_file():
    """Verify containers appear correctly in golden file."""

    # Run ingestion
    run_datahub_cmd(["ingest", "-c", str(config_file)], tmp_path=tmp_path)

    # Load golden file
    with open(golden_file) as f:
        mces = json.load(f)

    # Check database container exists
    database_container_urns = [
        mce["proposedSnapshot"]["urn"]
        for mce in mces
        if mce["proposedSnapshot"]["type"] == "container"
        and "database" in mce["proposedSnapshot"]["urn"]
    ]
    assert len(database_container_urns) > 0

    # Check schema container has parent reference
    schema_containers = [
        mce for mce in mces
        if mce["proposedSnapshot"]["type"] == "container"
        and "schema" in mce["proposedSnapshot"]["urn"]
    ]

    for container in schema_containers:
        aspects = container["proposedSnapshot"]["aspects"]
        container_aspect = next(
            a for a in aspects if a.get("com.linkedin.container.Container")
        )
        # Verify parent container is set
        assert container_aspect["com.linkedin.container.Container"]["container"]
```

---

## Quick Reference

### Choose Your Pattern

| Pattern               | When to Use                              | Pros                                     | Cons                         |
| --------------------- | ---------------------------------------- | ---------------------------------------- | ---------------------------- |
| `gen_containers()`    | Most sources, SQL databases, API sources | Fine control, widely used, many examples | More verbose                 |
| SDK `Container` class | Newer sources, OOP style                 | Cleaner API, automatic parent resolution | Fewer examples, less control |

### Container Creation Checklist

- [ ] Define container key class (or use built-in)
- [ ] Use `gen_containers()` or SDK `Container` class
- [ ] Include proper subtypes
- [ ] Set parent container key for child containers
- [ ] Add external URLs when available
- [ ] Add descriptions and custom properties
- [ ] Link datasets to containers using `add_dataset_to_container()` or `ContainerClass`
- [ ] Track processed containers to avoid duplicates
- [ ] Emit containers before datasets
- [ ] Test container hierarchy in integration tests

### Common Imports

```python
# For gen_containers pattern:
from datahub.emitter.mcp_builder import (
    ContainerKey,
    DatabaseKey,
    SchemaKey,
    gen_containers,
    add_dataset_to_container,
)
from datahub.ingestion.source.common.subtypes import (
    DatasetContainerSubTypes,
    BIContainerSubTypes,
)

# For SDK Container pattern:
from datahub.emitter.mcp_builder import ContainerKey
from datahub.sdk.container import Container

# For linking entities to containers:
from datahub.metadata.schema_classes import ContainerClass
from datahub.emitter.mcp import MetadataChangeProposalWrapper
```

---

## Real-World Examples

### Example Sources Using `gen_containers()`:

- `src/datahub/ingestion/source/sql/sql_utils.py` - SQL databases and schemas
- `src/datahub/ingestion/source/aws/glue.py` - AWS Glue databases
- `src/datahub/ingestion/source/nifi.py` - NiFi process groups
- `src/datahub/ingestion/source/mode.py` - Mode spaces
- `src/datahub/ingestion/source/data_lake_common/data_lake_utils.py` - Folders and buckets

### Example Sources Using SDK `Container` Class:

- `src/datahub/ingestion/source/lightdash/lightdash.py` - Lightdash projects and spaces

### Example Source with INCORRECT Pattern (DO NOT FOLLOW):

- `src/datahub/ingestion/source/snowplow/snowplow.py` - ❌ Manually emits `ContainerPropertiesClass` (incorrect)

---

## Summary

1. **Use `gen_containers()` or SDK `Container` class** - these are the only correct approaches
2. **Define container keys** - use built-in keys when available or create custom subclasses
3. **Establish parent-child relationships** - via `parent_container_key` parameter or key hierarchy
4. **Link datasets to containers** - using `add_dataset_to_container()` or `ContainerClass`
5. **Never manually emit container aspects** - use the provided helper functions
6. **Test your container hierarchy** - verify in integration tests and golden files

Following these patterns ensures your containers integrate correctly with DataHub's browse path system, search, and UI navigation.
