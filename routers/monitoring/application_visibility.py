from modulefinder import test
from typing import Literal, Optional
from fastapi import APIRouter, Query, Depends
from config import require_credentials
from models import ApplicationVisibility
from services.central_service import get_conn
from utils import paginated_fetch, groups_to_map, compute_time_window
from datetime import datetime, timedelta, timezone

APPLICATION_LIMIT = 1000

router = APIRouter(
    prefix="/application_visibility",
    tags=["application_visibility"],
    dependencies=[Depends(require_credentials)],
)


@router.get(
    "",
    operation_id="get_application_visibility",
    summary="Get applications accessed within a site with advanced filtering",
    response_model=list[ApplicationVisibility],
)
async def get_application_visibility(
    site_id: str = Query(..., description="Site ID to filter applications."),
    time_range: Literal[
        "last_1h", "last_6h", "last_24h", "last_7d", "last_30d", "today", "yesterday"
    ] = Query("last_1h", description="Predefined time window"),
    client_id: str | None = Query(
        None, description="Client MAC address to filter applications."
    ),
    category: Optional[
        Literal[
            "Antivirus",
            "Business and Economy",
            "Computer and Internet Info",
            "Computer and Internet Security",
            "Encrypted",
            "Internet Communications",
            "Network Service",
            "Office365 SAAS",
            "Standard",
            "Web",
        ]
    ] = Query(
        None,
        description="Filter by application category. Supported values: Antivirus, Business and Economy, Computer and Internet Info, Computer and Internet Security, Encrypted, Internet Communications, Network Service, Office365 SAAS, Standard, Web.",
    ),
    state: Optional[Literal["allowed", "partial", "blocked"]] = Query(
        None,
        description="Filter by application state. Supported values: allowed, partial, blocked.",
    ),
    risk: Optional[
        Literal["Low", "High", "Suspicious", "Moderate", "Trustworthy", "Not Evaluated"]
    ] = Query(
        None,
        description="Filter by application risk level. Supported values: Low, High, Suspicious, Moderate, Trustworthy, Not Evaluated.",
    ),
    tls_version: Optional[Literal["TLS 1.0", "TLS 1.1", "TLS 1.2", "TLS 1.3"]] = Query(
        None,
        description="Filter by TLS version used by the application. Supported values: TLS 1.0, TLS 1.1, TLS 1.2, TLS 1.3.",
    ),
    host_type: Optional[Literal["Hybrid", "Private", "Public"]] = Query(
        None,
        description="Filter by application host type. Supported values: Hybrid, Private, Public.",
    ),
    country: Optional[str] = Query(
        None,
        description="Filter by country where the application's server is located. Use country code, for example: IN.",
    ),
    role: Optional[str] = Query(
        None, description="Applications based on their assigned roles"
    ),
) -> list[ApplicationVisibility]:
    """
    Purpose: Return a list of applications accessed in a site by all clients or for a specific client within a specified time range, along with their details and metadata.

    ## Query Parameters:
    - **site_id** (string): Filter by site ID
    - **time_range** (string, optional): Predefined time window for filtering applications. Supported values: last_1h, last_6h, last_24h, last_7d, last_30d, today, yesterday. Default is last_1h.
    - **client_id** (string, optional): Client MAC address to filter applications.
    - **category** (string, optional): Filter by application category. Supported values: Antivirus, Business and Economy, Computer and Internet Info, Computer and Internet Security, Encrypted, Internet Communications, Network Service, Office365 SAAS, Standard, Web.
    - **state** (string, optional): Filter by application state. Supported values: allowed, partial, blocked.
    - **risk** (string, optional): Filter by application risk level. Supported values: Low, High, Suspicious, Moderate, Trustworthy, Not Evaluated.
    - **tls_version** (string, optional): Filter by TLS version used by the application. Supported values: TLS 1.0, TLS 1.1, TLS 1.2, TLS 1.3.
    - **host_type** (string, optional): Filter by application host type. Supported values: Hybrid, Private, Public.
    - **country** (string, optional): Filter by country where the application's server is located. Use country code, for example: IN.
    - **role** (string, optional): Applications based on their assigned roles

    ## Response: List of applications with details such as application name, category, state, risk level, TLS version, host type, country, role, and other metadata.

    **200**: Successful Response
    Returns a list of applications accessed within a site with the following attributes for each application:
        - **experience** (dict): Experience metrics related to the application. The structure of this field will include number of clients experiencing poor, fair, & good experience for this application along with the total number of clients. The metrics may vary and can include various performance and user experience metrics provided by Central.
        - **dest_location** (list): Locations where the application or website is hosted
        - **risk** (string): Security risk level of the application.
        - **application_host_type** (string): Host type of the application.
        - **name** (string): Name of the application.
        - **tx_bytes** (int): Transmitted bytes for the application.
        - **rx_bytes** (int): Received bytes for the application.
        - **last_used_time** (string): Last used timestamp of the application within the specified time range.
        - **tls_version** (string): TLS version used by the application.
    """
    start_dt, end_dt = compute_time_window(time_range)

    start_query_time = int(start_dt.timestamp() * 1000)
    end_query_time = int(end_dt.timestamp() * 1000)
    print(
        f"Computed time window - Start: {start_dt} ({start_query_time}), End: {end_dt} ({end_query_time})"
    )
    query_params = {
        "site-id": site_id,
        "start-query-time": str(start_query_time),
        "end-query-time": str(end_query_time),
    }
    if client_id:
        query_params["client-id"] = client_id
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

    if category:
        add_filter("category", category)

    if state:
        add_filter("state", state)

    if risk:
        add_filter("risk", risk)

    if tls_version:
        add_filter("tls_version", tls_version)

    if host_type:
        add_filter("host_type", host_type)

    if country:
        add_filter("country", country)

    if role:
        add_filter("role", role)

    if filter_parts:
        query_params["filter"] = " and ".join(filter_parts)
    # Use the generic paginated_fetch helper to collect items
    applications = paginated_fetch(
        get_conn(),
        "network-monitoring/v1alpha1/applications",
        APPLICATION_LIMIT,
        additional_params=query_params,
        use_cursor=False,
        different_response_key="applications",
    )

    return [
        clean_application_visibility_data(app) for app in applications
    ]  # Filter out entries without a name


def clean_application_visibility_data(applications: dict) -> None:
    """Clean and transform application visibility data to ensure consistent formatting and handle missing values. For each application in the input list, this function will: - Ensure all expected fields are present, filling in None for any missing fields. - Standardize field names and formats as needed. - Handle any necessary data transformations (e.g., converting timestamps to human-readable format). Args: applications (list): List of application data dictionaries as returned by the API. Returns: list: Cleaned and standardized list of application data dictionaries."""
    # return ApplicationVisibility(
    #     experience=groups_to_map(applications.get("experience"))
    # )
