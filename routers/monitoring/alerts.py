from fastapi import APIRouter, Query, Depends
from typing import List, Optional, Literal
from config import require_credentials
from models import Alert
from utils import paginated_fetch
from services.central_service import get_conn

ALERT_LIMIT = 100  # Default limit for alerts if not specified in query parameters
router = APIRouter(
    prefix="/alerts", tags=["alerts"], dependencies=[Depends(require_credentials)]
)


@router.get("", operation_id="filter_alerts", response_model=List[Alert])
async def get_alerts(
    site_id: str = Query(..., description="Site ID to filter alerts for."),
    deviceType: Optional[
        Literal["Access Point", "Gateway", "Switch", "Bridge"]
    ] = Query(
        None,
        description="Filter alerts by device type. Supported values: Access Point, Gateway, Switch, Bridge.",
    ),
    category: Optional[
        Literal[
            "Clients", "System", "LAN", "WLAN", "WAN", "Cluster", "Routing", "Security"
        ]
    ] = Query(
        None,
        description=(
            "Filter alerts by category. Supported values: Clients, System, LAN, WLAN, WAN, Cluster, Routing, Security."
        ),
    ),
) -> List[Alert]:
    """
    Purpose: Return a filtered list of active alerts for a specific site with optional filtering by device type and category.

    Instructions for AI/LLM:
    - Use this endpoint to retrieve active alerts AFTER calling get_site_name_id_mapping to obtain the site_id
    - When users ask about "issues", "problems", "warnings", or "what's wrong", call this endpoint
    - Prioritize alerts by severity (Critical > High > Medium > Low) and recency (createdAt timestamp)
    - For network troubleshooting workflows: 1) Call get_sites, 2) Identify sites with high alert counts, 3) Call this endpoint with site_id
    - DO NOT provide recommendations or remediation steps that are not directly supported by the alert data. Base all insights strictly on the alert attributes (summary, category, severity, etc.) & API Responses

    Prerequisites:
    - Requires site_id from get_site_name_id_mapping endpoint
    - User must have valid credentials (automatically enforced via dependency)

    Performance Notes:
    - Lightweight operation, safe to call frequently
    - Returns only active alerts (status='Active'), cleared alerts are excluded
    - Results are automatically sorted by creation time (newest first)
    - Maximum 100 alerts returned per request (pagination handled automatically)

    ## Query Parameters:

    - **site_id** (string, required): Site identifier obtained from get_sites. Used to filter alerts to a specific site location.

    - **deviceType** (string, optional): Filter by network device type. Supported values:
        - "Access Point" - Wireless access points and Wi-Fi infrastructure
        - "Gateway" - Network gateways and security appliances
        - "Switch" - Wired network switches
        - "Bridge" - Wireless or wired bridge devices
      Example: deviceType="Access Point" returns only AP-related alerts

    - **category** (string, optional): Filter by alert category/domain. Supported values:
        - "Clients" - Client connectivity and authentication issues
        - "System" - System-level errors, hardware failures, resource exhaustion
        - "LAN" - Local area network and wired connectivity issues
        - "WLAN" - Wireless network issues (coverage, interference, channel quality)
        - "WAN" - Wide area network and internet connectivity issues
        - "Cluster" - Clustering and high availability issues
        - "Routing" - Routing protocol and path issues
        - "Security" - Security threats, policy violations, intrusion attempts
      Example: category="WLAN" returns only wireless network alerts

    ## Responses:

    **200**: Successful Response
    Returns a list of active alerts with the following attributes:

        - **summary** (string, required): Human-readable alert description with specific details (device name, metrics, thresholds, duration)
          Example: "AP BO-BOM-AP01 channel quality was 64% for 30 minutes on the 5 GHz channel 44 which is lower than the threshold of 70%."

        - **name** (string, required): Alert type/title. Used to identify the specific alert condition.
          Example: "5 GHz Channel Quality", "DHCP Failure", "Device Offline"

        - **category** (string, required): Alert category as described in query parameters.
          Values: Clients, System, LAN, WLAN, WAN, Cluster, Routing, Security

        - **severity** (string, required): Alert severity level indicating impact.
          Values: "Critical", "High", "Medium", "Low"
          Critical = Service impacting, immediate action required
          High = Significant degradation, action required soon
          Medium = Noticeable issues, investigate when possible
          Low = Minor anomalies, informational

        - **priority** (string, required): Business priority level for alert handling.
          Values: "Very High", "High", "Medium", "Low"
          Used for alert queue prioritization and SLA tracking

        - **status** (string, required): Current alert state. Always "Active" for this endpoint.
          Note: Cleared alerts are excluded from results

        - **deviceType** (string, optional): Type of device associated with alert.
          Values: "Access Point", "Gateway", "Switch", "Bridge", null (for site-wide alerts)

        - **createdAt** (string, required): ISO 8601 timestamp when alert was first triggered.
          Format: "2026-02-11T12:01:35.044Z" (UTC timezone)
          Used for determining alert age and sorting by recency

        - **updatedAt** (string, optional): ISO 8601 timestamp of last alert update.
          null if alert hasn't been updated since creation
          Updates occur when alert conditions change or are acknowledged

        - **updatedBy** (string, optional): Identifier of user who last updated the alert.
          null for system-generated updates
          Contains user email or system identifier for manual updates

        - **clearedReason** (string, optional): Reason the alert was cleared. Always null for active alerts.
          Populated only when status="Cleared" (which is filtered out by this endpoint)

    **400**: Bad Request
    - Invalid site_id format
    - Unsupported deviceType or category value
    - Malformed filter syntax

    **401**: Unauthorized
    - Missing authentication credentials
    - Invalid or expired access token
    - Insufficient permissions for site access

    **404**: Not Found
    - Specified site_id does not exist in account
    - Site_id exists but user lacks access permissions

    **429**: Rate Limited
    - Too many API requests in time window
    - Retry after delay indicated in response headers

    ## Example Request:
    ```
    GET /alerts?site_id=3917546799&deviceType=Access%20Point&category=WLAN
    ```
    Retrieves all active WLAN alerts from Access Points at site 3917546799

    ## Example Response:
    ```json
    [
        {
            "summary": "AP BO-BOM-AP01 channel quality was 64% for 30 minutes on the 5 GHz channel 44 which is lower than the threshold of 70%.",
            "clearedReason": null,
            "createdAt": "2026-02-11T12:01:35.044Z",
            "priority": "Very High",
            "updatedAt": "2026-02-11T12:31:35.044Z",
            "deviceType": "Access Point",
            "updatedBy": null,
            "name": "5 GHz Channel Quality",
            "status": "Active",
            "category": "WLAN",
            "severity": "Critical"
        },
        {
            "summary": "AP BO-BOM-AP02 has been offline for 45 minutes.",
            "clearedReason": null,
            "createdAt": "2026-02-11T11:15:22.033Z",
            "priority": "High",
            "updatedAt": null,
            "deviceType": "Access Point",
            "updatedBy": null,
            "name": "Device Offline",
            "status": "Active",
            "category": "System",
            "severity": "High"
        }
    ]
    ```

    ## Related Endpoints:
    - **get_sites**: Call FIRST to get site_id and see alert counts per site
    - **filter_devices**: Get device details for alerts associated with specific devices
    - **filter_clients**: Investigate client-category alerts to see affected clients

    ## Common Use Cases:

    1. **Network Health Check Workflow:**
       - Call get_sites to see overview with alert counts
       - Identify sites with Critical alerts > 0
       - Call get_alerts with site_id to get alert details
       - Provide remediation based on alert category and severity

    2. **Device-Specific Troubleshooting:**
       - User reports "AP issues"
       - Call get_alerts with deviceType="Access Point" and category="WLAN"
       - Analyze alerts for patterns (multiple APs, same channel, same issue)
       - Provide targeted remediation (channel change, firmware update, etc.)

    3. **Security Incident Response:**
       - Call get_alerts with category="Security"
       - Sort by severity and createdAt
       - Identify attack patterns or policy violations
       - Recommend security actions (block client, update policy, investigate logs)

    4. **Proactive Monitoring:**
       - Periodic calls to get_alerts for critical sites
       - Track alert trends over time (increasing/decreasing)
       - Alert on new Critical severity alerts
       - Generate health reports with alert summaries
    """

    # Build query params to send to Central
    filter_parts = []

    def add_filter(field: str, value: str):
        """Add filter expression - uses 'in' for comma-separated values, 'eq' for single values"""
        if "," in value:
            # Multiple values - use 'in' operator
            values_list = [v.strip() for v in value.split(",")]
            values_str = ",".join(f"'{v}'" for v in values_list)
            filter_parts.append(f"{field} in ({values_str})")
        else:
            # Single value - use 'eq' operator
            filter_parts.append(f"{field} eq '{value}'")

    add_filter("status", "Active")  # Status filter is always added as "Active"

    if site_id:
        add_filter("siteId", site_id)
    if deviceType:
        add_filter("deviceType", deviceType)
    if category:
        add_filter("category", category)

    # Build query parameters
    query_params = {"sort": "createdAt desc"}

    if filter_parts:
        query_params["filter"] = " and ".join(filter_parts)

    # Use the generic paginated_fetch helper to collect items
    alerts = paginated_fetch(
        get_conn(),
        "network-notifications/v1alpha1/alerts",
        ALERT_LIMIT,
        additional_params=query_params,
        use_cursor=True,
    )

    return alerts


def clean_alert_data(alert: dict) -> Alert:
    """Helper function to clean and standardize alert data from Central API response"""
    return Alert(
        summary=alert.get("summary", ""),
        clearedReason=alert.get("clearedReason"),
        createdAt=alert.get("createdAt", ""),
        priority=alert.get("priority", ""),
        updatedAt=alert.get("updatedAt"),
        deviceType=alert.get("deviceType"),
        updatedBy=alert.get("updatedBy"),
        name=alert.get("name"),
        status=alert.get("status"),
        category=alert.get("category"),
        severity=alert.get("severity"),
    )
