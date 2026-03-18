from fastapi import APIRouter, Query, Depends
from typing import Optional, Literal
from services.central_service import get_conn
from config import require_credentials
from utils import paginated_fetch, compute_time_window
from models import Event

router = APIRouter(
    prefix="/events", tags=["events"], dependencies=[Depends(require_credentials)]
)


@router.get("", operation_id="get_events", response_model=list[Event])
async def get_events(
    context_type: Literal[
        "SITE",
        "ACCESS_POINT",
        "SWITCH",
        "GATEWAY",
        "WIRELESS_CLIENT",
        "WIRED_CLIENT",
        "BRIDGE",
    ] = Query(
        ...,
        description="Type of context (SITE, ACCESS_POINT, SWITCH, GATEWAY, WIRELESS_CLIENT, WIRED_CLIENT, BRIDGE).",
    ),
    context_identifier: str = Query(
        ...,
        max_length=128,
        description="Context Identifier (site ID, device serial number or client MAC address).",
    ),
    time_range: Literal[
        "last_1h", "last_6h", "last_24h", "last_7d", "last_30d", "today", "yesterday"
    ] = Query("last_1h", description="Predefined time window"),
    site_id: str = Query(
        ...,
        max_length=128,
        description="Site ID to filter the event details for a specific site.",
    ),
    search: Optional[str] = Query(
        None,
        max_length=256,
        description="Search events by name, serial number, host name, client MAC address or device MAC address. Search is restricted to the metadata.",
    ),
):
    """
    Retrieve events for a given context (site, device, or client) within a specified time range.

    ## Query Parameters:

    - **context_type** (string, required): Type of context entity. This is specifying what the context_identifier refers to. Allowed values:
        SITE, ACCESS_POINT, SWITCH, GATEWAY, WIRELESS_CLIENT, WIRED_CLIENT, BRIDGE

    - **context_identifier** (string, required): Identifier for the context — site ID, device serial number, or client MAC address. If context_type is SITE, this should be the site ID. If context_type is a device type (e.g. ACCESS_POINT), this should be the device serial number. If context_type is a client type (e.g. WIRELESS_CLIENT), this should be the client MAC address.

    - **time_range** (string, required): Predefined time window for the events. Allowed values: last_1h, last_6h, last_24h, last_7d, last_30d, today, yesterday. The time range is relative to the current time.

    - **site_id** (string, required): Site ID to scope events to a specific site. This is required to ensure that the events returned are relevant to the specified site, especially when context_type is not SITE.

    - **search** (string, optional): Search events by name, serial number, host name, client MAC address or device MAC address. Full text search is not supported. Search is restricted to the metadata.

    ## Responses:

    **200**: Successful Response — returns a list of event objects.
    """
    start_dt, end_dt = compute_time_window(time_range)

    query_params = {
        "context-type": context_type,
        "context-identifier": context_identifier,
        "start-at": start_dt.strftime("%Y-%m-%dT%H:%M:%S.")
        + f"{start_dt.microsecond // 1000:03d}Z",
        "end-at": end_dt.strftime("%Y-%m-%dT%H:%M:%S.")
        + f"{end_dt.microsecond // 1000:03d}Z",
        "site-id": site_id,
    }
    print(
        f"Computed time window - Start: {query_params['start-at']}, End: {query_params['end-at']}"
    )
    if search:
        query_params["search"] = search
    events = paginated_fetch(
        get_conn(),
        "network-troubleshooting/v1/events",
        1000,
        additional_params=query_params,
        use_cursor=True,
        items_key="events",
    )
    return [Event(**event) for event in events]
