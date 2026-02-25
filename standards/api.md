# Writing a New API-Based Source

This guide covers implementing REST/GraphQL API-based sources for systems that expose metadata through APIs rather than SQL interfaces.

## Related Guides

- [Main Guide](main.md) - Overview and quick start
- [Code Style](code_style.md) - Code formatting, naming, type safety
- [SQL Sources](sql.md) - For SQL database and data warehouse sources
- [Common Patterns](patterns.md) - Shared patterns and utilities
- [Lineage Extraction](lineage.md) - Implementing lineage
- [Performance](performance.md) - Performance and memory optimization
- [Testing](testing.md) - Testing strategies
- [Registration & Documentation](registration.md) - Final steps

## When to Use This Pattern

Use the API-based source pattern when:

1. **The system exposes metadata through a REST or GraphQL API** (not SQL/JDBC)
2. **The system doesn't have a traditional database schema layer** (databases, schemas, tables)
3. **You need to extract non-tabular entities** (dashboards, ML models, pipelines, users)

### Common Examples

- **BI Tools** - Tableau, Looker, Power BI (extract dashboards, charts, and lineage via APIs)
- **Data Lakes** - AWS S3, GCS, ADLS (extract files and object metadata)
- **Orchestration Tools** - Airflow, Prefect, Dagster (extract DAGs and pipelines)
- **ML Platforms** - MLflow, SageMaker (extract models and experiments)
- **Identity Systems** - Okta, Azure AD (extract users and groups)
- **NoSQL Databases** - MongoDB, Cassandra (when using their REST APIs instead of SQL drivers)
- **Streaming Platforms** - Kafka (extract topics and schemas via REST APIs)

### When NOT to Use This Pattern

**Use the SQL-based pattern instead** ([sql.md](sql.md)) when:

- The system has a SQL/JDBC interface (Snowflake, Postgres, MySQL, Redshift, BigQuery)
- The system organizes data in databases/schemas/tables
- You can query metadata using SQL (information_schema, system catalogs)

> **Note**: Some systems support **both** SQL and API access (e.g., Snowflake). Choose based on what metadata you need to extract. Use SQL for table/column metadata, use APIs for usage stats or governance features.

## DataHub Entity Types for API Sources

When implementing an API-based source, you'll typically emit these entity types:

### Core Entities

- **Dashboards** - BI dashboards and reports
- **Charts** - Individual visualizations
- **DataFlow** - Orchestration DAGs and pipelines
- **DataJob** - Individual pipeline tasks
- **MLModel** - Machine learning models
- **MLModelGroup** - Model registries
- **MLFeatureTable** - Feature store tables
- **MLFeature** - Individual features
- **CorpUser** - User accounts
- **CorpGroup** - Teams and groups
- **Containers** - Workspaces, projects, folders, buckets

### Supporting Aspects

- **Ownership** - Who owns/created the entity
- **Tags** - Custom labels and classifications
- **Glossary Terms** - Business terminology
- **Domains** - Logical groupings
- **Lineage** - Upstream/downstream relationships (see [lineage.md](lineage.md))
- **Usage Statistics** - View counts, user engagement

### Architecture Overview

```
YourSource
    ↓ extends
StatefulIngestionSourceBase + TestableSource
    ↓ provides
- Stateful ingestion (checkpointing)
- Deletion detection
- State management
- Report aggregation
```

### Step-by-Step Implementation

#### 1. Create Configuration Class

```python
from typing import Optional, Dict
from pydantic import Field, validator
import pydantic

from datahub.configuration.common import AllowDenyPattern, ConfigModel
from datahub.configuration.source_common import (
    PlatformInstanceConfigMixin,
    EnvConfigMixin,
)
from datahub.ingestion.source.state.stale_entity_removal_handler import (
    StatefulStaleMetadataRemovalConfig,
)
from datahub.ingestion.source.state.stateful_ingestion_base import (
    StatefulIngestionConfigBase,
)

class MyAPIConnectionConfig(ConfigModel):
    """Connection configuration for API"""

    # API endpoint
    api_url: str = Field(
        description="Base URL for API (e.g., 'https://api.myplatform.com')"
    )

    # Authentication
    api_key: Optional[pydantic.SecretStr] = Field(
        default=None,
        description="API key for authentication"
    )

    username: Optional[str] = Field(
        default=None,
        description="Username (for basic auth)"
    )

    password: Optional[pydantic.SecretStr] = Field(
        default=None,
        description="Password (for basic auth)"
    )

    # OAuth
    client_id: Optional[str] = Field(
        default=None,
        description="OAuth client ID"
    )

    client_secret: Optional[pydantic.SecretStr] = Field(
        default=None,
        description="OAuth client secret"
    )

    # Connection options
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds"
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )

    @validator("api_url")
    def api_url_must_be_valid(cls, v):
        """Validate API URL format"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("API URL must start with http:// or https://")
        return v.rstrip("/")  # Remove trailing slash


class MyAPISourceConfig(
    StatefulIngestionConfigBase,
    PlatformInstanceConfigMixin,
    EnvConfigMixin,
):
    """Configuration for MyAPI source"""

    connection: MyAPIConnectionConfig = Field(
        description="Connection configuration"
    )

    # Filtering patterns
    dashboard_pattern: AllowDenyPattern = Field(
        default=AllowDenyPattern.allow_all(),
        description="Regex patterns for dashboards to filter"
    )

    chart_pattern: AllowDenyPattern = Field(
        default=AllowDenyPattern.allow_all(),
        description="Regex patterns for charts to filter"
    )

    # Feature flags
    extract_ownership: bool = Field(
        default=True,
        description="Whether to extract ownership information"
    )

    extract_usage_stats: bool = Field(
        default=False,
        description="Whether to extract usage statistics (requires additional permissions)"
    )

    extract_lineage: bool = Field(
        default=True,
        description="Whether to extract lineage information"
    )

    # Lookback window for usage stats
    usage_lookback_days: int = Field(
        default=7,
        description="Number of days to look back for usage statistics"
    )

    # Stateful ingestion
    stateful_ingestion: Optional[StatefulStaleMetadataRemovalConfig] = Field(
        default=None,
        description="Stateful ingestion configuration"
    )
```

#### 2. Create API Client Wrapper

**Best Practice**: Separate API client from source logic

```python
import requests
from typing import List, Dict, Any, Optional, Iterator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


class MyAPIClient:
    """
    Wrapper around MyAPI REST API.

    Handles:
    - Authentication
    - Request retry logic
    - Pagination
    - Rate limiting
    - Error handling
    """

    def __init__(self, config: MyAPIConnectionConfig):
        self.config = config
        self.base_url = config.api_url

        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=1,  # Exponential backoff: 1, 2, 4 seconds
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Setup authentication
        self._setup_auth()

    def _setup_auth(self):
        """Configure authentication headers"""
        if self.config.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.api_key.get_secret_value()}"
            })
        elif self.config.username and self.config.password:
            self.session.auth = (
                self.config.username,
                self.config.password.get_secret_value()
            )
        elif self.config.client_id and self.config.client_secret:
            # OAuth flow
            token = self._get_oauth_token()
            self.session.headers.update({
                "Authorization": f"Bearer {token}"
            })

    def _get_oauth_token(self) -> str:
        """Get OAuth access token"""
        response = requests.post(
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret.get_secret_value(),
            },
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return {}
            elif e.response.status_code == 403:
                logger.error(f"Permission denied: {url}")
                raise PermissionError(f"Permission denied for {url}")
            else:
                logger.error(f"HTTP error {e.response.status_code}: {url}")
                raise
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {url}: {e}")
            raise

    def _paginated_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
    ) -> Iterator[Dict[str, Any]]:
        """
        Make paginated API request.

        Yields individual items from all pages.
        Adapt pagination logic to your API's pattern.
        """
        params = params or {}
        params["page_size"] = page_size
        page = 1

        while True:
            params["page"] = page
            response = self._request("GET", endpoint, params=params)

            # Adapt to your API's response structure
            items = response.get("items", [])
            if not items:
                break

            for item in items:
                yield item

            # Check if there are more pages
            if not response.get("has_more", False):
                break

            page += 1

    # API-specific methods

    def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all workspaces"""
        return list(self._paginated_request("/workspaces"))

    def get_dashboards(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get dashboards in workspace"""
        return list(self._paginated_request(
            f"/workspaces/{workspace_id}/dashboards"
        ))

    def get_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """Get single dashboard details"""
        return self._request("GET", f"/dashboards/{dashboard_id}")

    def get_dashboard_lineage(self, dashboard_id: str) -> List[Dict[str, Any]]:
        """Get lineage for dashboard"""
        return self._request("GET", f"/dashboards/{dashboard_id}/lineage").get("tables", [])

    def get_usage_stats(
        self,
        resource_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Get usage statistics"""
        return self._request(
            "GET",
            f"/usage/{resource_id}",
            params={"start_date": start_date, "end_date": end_date}
        )

    def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            self._request("GET", "/ping")
            return True
        except Exception:
            return False

    def get_permissions(self) -> List[str]:
        """Get available API permissions for current user"""
        response = self._request("GET", "/permissions")
        return response.get("permissions", [])
```

#### 3. Implement Source Class

```python
from datetime import datetime, timedelta
from typing import Iterable, List, Dict, Any

from datahub.emitter.mce_builder import (
    make_dashboard_urn,
    make_chart_urn,
    make_dataset_urn,
    make_user_urn,
)
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.api.decorators import (
    capability,
    config_class,
    platform_name,
    support_status,
)
from datahub.ingestion.api.source import (
    CapabilityReport,
    SourceCapability,
    TestableSource,
    TestConnectionReport,
)
from datahub.ingestion.api.workunit import MetadataWorkUnit
from datahub.ingestion.source.state.stale_entity_removal_handler import (
    StaleEntityRemovalHandler,
    StaleEntityRemovalSourceReport,
)
from datahub.ingestion.source.state.stateful_ingestion_base import (
    StatefulIngestionSourceBase,
)
from datahub.metadata.schema_classes import (
    ChangeTypeClass,
    DashboardInfoClass,
    ChartInfoClass,
    UpstreamClass,
    UpstreamLineageClass,
    OwnershipClass,
    OwnerClass,
    OwnershipTypeClass,
)


@platform_name("MyAPI")
@config_class(MyAPISourceConfig)
@support_status(SupportStatus.INCUBATING)
@capability(SourceCapability.DESCRIPTIONS, "Enabled by default")
@capability(SourceCapability.LINEAGE_COARSE, "Enabled by default")
@capability(SourceCapability.USAGE_STATS, "Optionally enabled via configuration")
@capability(SourceCapability.OWNERSHIP, "Enabled by default")
@capability(SourceCapability.DELETION_DETECTION, "Enabled via stateful ingestion")
class MyAPISource(StatefulIngestionSourceBase, TestableSource):
    """
    Ingests metadata from MyAPI platform.

    Extracts:
    - Workspaces (as containers)
    - Dashboards
    - Charts
    - Lineage (dashboard -> datasets)
    - Ownership
    - Usage statistics (optional)
    """

    def __init__(self, config: MyAPISourceConfig, ctx: PipelineContext):
        super().__init__(config, ctx)
        self.config = config
        self.report = StaleEntityRemovalSourceReport()

        # Initialize API client
        self.api_client = MyAPIClient(config.connection)

        # Initialize stale entity removal handler
        self.stale_entity_removal_handler = StaleEntityRemovalHandler.create(
            self, self.config, self.ctx
        )

    @classmethod
    def create(cls, config_dict: dict, ctx: PipelineContext) -> "MyAPISource":
        config = MyAPISourceConfig.parse_obj(config_dict)
        return cls(config, ctx)

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        """
        Main extraction logic.

        Order matters for deletion detection:
        1. Emit all entities
        2. Emit lineage
        3. Stale entity removal happens automatically
        """
        # Get all workspaces
        workspaces = self.api_client.get_workspaces()

        for workspace in workspaces:
            # Emit workspace container
            yield from self._process_workspace(workspace)

            # Get dashboards in workspace
            dashboards = self.api_client.get_dashboards(workspace["id"])

            for dashboard in dashboards:
                # Filter by pattern
                if not self.config.dashboard_pattern.allowed(dashboard["name"]):
                    self.report.report_dropped(dashboard["name"])
                    continue

                # Process dashboard
                yield from self._process_dashboard(dashboard, workspace)

        # Process usage statistics if enabled
        if self.config.extract_usage_stats:
            yield from self._process_usage_stats()

    def _process_workspace(self, workspace: Dict[str, Any]) -> Iterable[MetadataWorkUnit]:
        """
        Emit workspace as container.

        Containers group related entities (dashboards, datasets, etc.)
        """
        from datahub.metadata.schema_classes import (
            ContainerClass,
            ContainerPropertiesClass,
        )

        workspace_urn = f"urn:li:container:{self.get_workspace_key(workspace['id'])}"

        # Container properties
        container_properties = ContainerPropertiesClass(
            name=workspace["name"],
            description=workspace.get("description"),
            customProperties={
                "workspace_id": workspace["id"],
                "created_at": workspace.get("created_at"),
            },
        )

        yield MetadataChangeProposalWrapper(
            entityUrn=workspace_urn,
            aspect=container_properties,
        ).as_workunit()

        # Container aspect
        container = ContainerClass(container=None)  # Top-level container

        yield MetadataChangeProposalWrapper(
            entityUrn=workspace_urn,
            aspect=container,
        ).as_workunit()

    def _process_dashboard(
        self,
        dashboard: Dict[str, Any],
        workspace: Dict[str, Any],
    ) -> Iterable[MetadataWorkUnit]:
        """Process single dashboard"""

        # Generate URN
        dashboard_urn = make_dashboard_urn(
            platform="myapi",
            dashboard_id=dashboard["id"],
        )

        # Dashboard info aspect
        dashboard_info = DashboardInfoClass(
            title=dashboard["name"],
            description=dashboard.get("description"),
            customProperties={
                "workspace_id": workspace["id"],
                "workspace_name": workspace["name"],
                "dashboard_url": dashboard.get("url"),
                "created_at": dashboard.get("created_at"),
                "updated_at": dashboard.get("updated_at"),
            },
            charts=[
                make_chart_urn("myapi", chart["id"])
                for chart in dashboard.get("charts", [])
            ],
            lastModified=self._parse_timestamp(dashboard.get("updated_at")),
        )

        yield MetadataChangeProposalWrapper(
            entityUrn=dashboard_urn,
            aspect=dashboard_info,
        ).as_workunit()

        # Ownership
        if self.config.extract_ownership and dashboard.get("owner"):
            ownership = self._create_ownership(dashboard["owner"])
            yield MetadataChangeProposalWrapper(
                entityUrn=dashboard_urn,
                aspect=ownership,
            ).as_workunit()

        # Lineage
        if self.config.extract_lineage:
            yield from self._process_dashboard_lineage(dashboard_urn, dashboard)

        # Container (link to workspace)
        from datahub.metadata.schema_classes import ContainerClass

        workspace_urn = f"urn:li:container:{self.get_workspace_key(workspace['id'])}"
        container = ContainerClass(container=workspace_urn)

        yield MetadataChangeProposalWrapper(
            entityUrn=dashboard_urn,
            aspect=container,
        ).as_workunit()

        # Process charts
        for chart in dashboard.get("charts", []):
            if self.config.chart_pattern.allowed(chart["name"]):
                yield from self._process_chart(chart, dashboard_urn)

    def _process_chart(
        self,
        chart: Dict[str, Any],
        dashboard_urn: str,
    ) -> Iterable[MetadataWorkUnit]:
        """Process single chart"""

        chart_urn = make_chart_urn("myapi", chart["id"])

        chart_info = ChartInfoClass(
            title=chart["name"],
            description=chart.get("description"),
            customProperties={
                "chart_type": chart.get("type"),
                "chart_url": chart.get("url"),
            },
            chartUrl=chart.get("url"),
            lastModified=self._parse_timestamp(chart.get("updated_at")),
        )

        yield MetadataChangeProposalWrapper(
            entityUrn=chart_urn,
            aspect=chart_info,
        ).as_workunit()

    def _process_dashboard_lineage(
        self,
        dashboard_urn: str,
        dashboard: Dict[str, Any],
    ) -> Iterable[MetadataWorkUnit]:
        """Extract dashboard lineage"""

        # Get lineage from API
        lineage_info = self.api_client.get_dashboard_lineage(dashboard["id"])

        if not lineage_info:
            return

        # Build upstream list
        upstreams = []
        for table in lineage_info:
            # Convert API table reference to DataHub URN
            # This depends on how your API represents table references
            dataset_urn = self._resolve_table_reference(table)
            if dataset_urn:
                upstreams.append(
                    UpstreamClass(
                        dataset=dataset_urn,
                        type=DatasetLineageTypeClass.TRANSFORMED,
                    )
                )

        if upstreams:
            lineage = UpstreamLineageClass(upstreams=upstreams)

            yield MetadataChangeProposalWrapper(
                entityUrn=dashboard_urn,
                aspect=lineage,
            ).as_workunit()

    def _resolve_table_reference(self, table_ref: Dict[str, Any]) -> Optional[str]:
        """
        Convert API table reference to DataHub dataset URN.

        This is critical for lineage - must match URNs from database sources.
        """
        # Example: API returns {"database": "prod", "schema": "public", "table": "users"}
        platform = table_ref.get("platform", "postgres")
        database = table_ref.get("database")
        schema = table_ref.get("schema")
        table = table_ref.get("table")

        if not all([database, schema, table]):
            return None

        # Construct dataset name matching SQL source format
        dataset_name = f"{database}.{schema}.{table}"

        return make_dataset_urn(
            platform=platform,
            name=dataset_name,
            env=self.config.env,
        )

    def _create_ownership(self, owner_info: Dict[str, Any]) -> OwnershipClass:
        """Create ownership aspect"""
        owners = []

        # Handle different owner formats from API
        if isinstance(owner_info, str):
            # Simple email string
            owner_urn = make_user_urn(owner_info)
            owners.append(
                OwnerClass(
                    owner=owner_urn,
                    type=OwnershipTypeClass.DATAOWNER,
                )
            )
        elif isinstance(owner_info, dict):
            # Structured owner object
            owner_urn = make_user_urn(owner_info["email"])
            owners.append(
                OwnerClass(
                    owner=owner_urn,
                    type=OwnershipTypeClass.DATAOWNER,
                )
            )

        return OwnershipClass(owners=owners)

    def _process_usage_stats(self) -> Iterable[MetadataWorkUnit]:
        """Extract usage statistics"""
        from datahub.metadata.schema_classes import (
            DatasetUsageStatisticsClass,
            DatasetFieldUsageCountsClass,
        )

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.config.usage_lookback_days)

        # Get all dashboards again for usage
        workspaces = self.api_client.get_workspaces()

        for workspace in workspaces:
            dashboards = self.api_client.get_dashboards(workspace["id"])

            for dashboard in dashboards:
                if not self.config.dashboard_pattern.allowed(dashboard["name"]):
                    continue

                # Get usage stats from API
                usage = self.api_client.get_usage_stats(
                    dashboard["id"],
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )

                dashboard_urn = make_dashboard_urn("myapi", dashboard["id"])

                # Convert to DataHub usage format
                usage_stats = DatasetUsageStatisticsClass(
                    timestampMillis=int(datetime.now().timestamp() * 1000),
                    eventGranularity=TimeWindowSizeClass(
                        unit=CalendarIntervalClass.DAY,
                        multiple=1,
                    ),
                    uniqueUserCount=usage.get("unique_users", 0),
                    totalSqlQueries=usage.get("view_count", 0),
                    topSqlQueries=[],  # Populate if available
                )

                yield MetadataChangeProposalWrapper(
                    entityUrn=dashboard_urn,
                    aspect=usage_stats,
                ).as_workunit()

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[int]:
        """Parse ISO timestamp to milliseconds"""
        if not timestamp_str:
            return None

        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except Exception:
            return None

    def get_workspace_key(self, workspace_id: str) -> str:
        """Generate stable key for workspace container"""
        return f"myapi.{workspace_id}"

    def get_report(self):
        return self.report

    @staticmethod
    def test_connection(config_dict: dict) -> TestConnectionReport:
        """Test connection to API"""
        test_report = TestConnectionReport()

        try:
            config = MyAPISourceConfig.parse_obj(config_dict)
            client = MyAPIClient(config.connection)

            # Test basic connectivity
            if client.test_connection():
                test_report.basic_connectivity = CapabilityReport(capable=True)
            else:
                test_report.basic_connectivity = CapabilityReport(
                    capable=False,
                    failure_reason="Failed to connect to API"
                )
                return test_report

            # Test permissions
            permissions = client.get_permissions()

            required_permissions = {"read:dashboards", "read:workspaces"}
            if required_permissions.issubset(set(permissions)):
                test_report.capability_report[SourceCapability.DESCRIPTIONS] = \
                    CapabilityReport(capable=True)
            else:
                missing = required_permissions - set(permissions)
                test_report.capability_report[SourceCapability.DESCRIPTIONS] = \
                    CapabilityReport(
                        capable=False,
                        failure_reason=f"Missing permissions: {', '.join(missing)}"
                    )

            # Test usage stats capability
            if config.extract_usage_stats:
                if "read:usage" in permissions:
                    test_report.capability_report[SourceCapability.USAGE_STATS] = \
                        CapabilityReport(capable=True)
                else:
                    test_report.capability_report[SourceCapability.USAGE_STATS] = \
                        CapabilityReport(
                            capable=False,
                            failure_reason="Missing 'read:usage' permission"
                        )

        except Exception as e:
            test_report.basic_connectivity = CapabilityReport(
                capable=False,
                failure_reason=str(e)
            )

        return test_report
```

### Common API Source Patterns

#### GraphQL API Pattern

```python
class GraphQLClient:
    def __init__(self, endpoint: str, auth_token: str):
        self.endpoint = endpoint
        self.headers = {"Authorization": f"Bearer {auth_token}"}

    def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        response = requests.post(
            self.endpoint,
            json={"query": query, "variables": variables},
            headers=self.headers,
        )
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result["data"]

    def get_dashboards_batch(self, workspace_ids: List[str]) -> List[Dict]:
        query = """
            query GetDashboards($workspaceIds: [ID!]!) {
                workspaces(ids: $workspaceIds) {
                    id
                    name
                    dashboards {
                        id
                        name
                        description
                        charts {
                            id
                            name
                        }
                    }
                }
            }
        """

        result = self.execute_query(query, {"workspaceIds": workspace_ids})
        return result["workspaces"]
```

#### Rate Limiting Pattern

```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = Lock()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # Remove old calls outside the period
                self.calls = [t for t in self.calls if now - t < self.period]

                if len(self.calls) >= self.max_calls:
                    # Wait until oldest call expires
                    sleep_time = self.period - (now - self.calls[0])
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    self.calls.pop(0)

                self.calls.append(now)

            return func(*args, **kwargs)

        return wrapper


class MyAPIClient:
    @RateLimiter(max_calls=100, period=60.0)  # 100 calls per minute
    def _request(self, method, endpoint, **kwargs):
        return self.session.request(method, endpoint, **kwargs)
```

## Required Aspects for API-Based Sources

**Every API source MUST emit these aspects. Missing aspects indicate INCOMPLETE implementation.**

### Understanding Aspect Requirements

- **✅ ALWAYS**: Must be emitted for every entity of this type
- **✅ IF SOURCE PROVIDES**: Must be emitted if the source system provides this information
- **✅ IF FEATURE ENABLED**: Must be emitted when the corresponding feature is enabled in config
- **🔄 AUTO-GENERATED**: Automatically generated by the pipeline from other aspects

### Auto-Generated Aspects (by DataHub Pipeline)

These aspects are automatically generated and do NOT need to be explicitly emitted:

| Aspect          | Generated From     | Notes                                   |
| --------------- | ------------------ | --------------------------------------- |
| `browsePathsV2` | `container` aspect | Auto-generated from container hierarchy |
| `status`        | All entities       | Auto-generated for all entities         |

### Required Aspects for Dashboards/Charts

| Aspect                 | Required              | Description                                                |
| ---------------------- | --------------------- | ---------------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS             | Links entity to data platform. **Always required.**        |
| `containerProperties`  | ✅ ALWAYS             | For workspaces/projects/folders                            |
| `subTypes`             | ✅ ALWAYS             | Identifies entity subtype (Dashboard, Chart, Report)       |
| `container`            | ✅ ALWAYS             | Links entities to parent containers                        |
| `dashboardInfo`        | ✅ IF DASHBOARD       | Dashboard metadata (required for all dashboards)           |
| `chartInfo`            | ✅ IF CHART           | Chart metadata (required for all charts)                   |
| `ownership`            | ✅ IF SOURCE PROVIDES | Dashboard/chart owners (required if source exposes owners) |
| `globalTags`           | ✅ IF SOURCE PROVIDES | Tags from source system (required if source has tags)      |

### Required Aspects for DataFlow/DataJob (Pipelines, ETL)

| Aspect                 | Required              | Description                                                 |
| ---------------------- | --------------------- | ----------------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS             | Links entity to data platform. **Always required.**         |
| `dataFlowInfo`         | ✅ ALWAYS             | Pipeline/flow metadata                                      |
| `dataJobInfo`          | ✅ ALWAYS             | Job/task metadata                                           |
| `dataJobInputOutput`   | ✅ ALWAYS             | Job input/output relationships (datasets and upstream jobs) |
| `globalTags`           | ✅ IF SOURCE PROVIDES | Tags from source system (required if source has tags)       |
| `ownership`            | ✅ IF SOURCE PROVIDES | Pipeline owners (required if source exposes owners)         |

### Common Mistakes

1. **Missing `dataPlatformInstance`**: This aspect is ALWAYS required, not just when `platform_instance` is configured. It links every entity to its data platform URN.

2. **Missing `ownership` when source has owners**: If the API returns owner/creator information, you MUST emit the `ownership` aspect.

3. **Missing `globalTags` when source has tags**: If the API returns tags/labels, you MUST emit them as `globalTags`.

4. **Missing `dataJobInputOutput` for jobs**: Every DataJob MUST have input/output relationships, even if empty.

### Example: Emitting dataPlatformInstance

```python
from datahub.emitter.mce_builder import (
    make_data_platform_urn,
    make_dataplatform_instance_urn,
)
from datahub.metadata.schema_classes import DataPlatformInstanceClass

def _emit_data_platform_instance(self, entity_urn: str) -> MetadataWorkUnit:
    """Always emit dataPlatformInstance - required for all entities."""
    instance_urn = None
    if self.config.platform_instance:
        instance_urn = make_dataplatform_instance_urn(
            self.platform, self.config.platform_instance
        )

    return MetadataChangeProposalWrapper(
        entityUrn=entity_urn,
        aspect=DataPlatformInstanceClass(
            platform=make_data_platform_urn(self.platform),
            instance=instance_urn,
        ),
    ).as_workunit()
```
