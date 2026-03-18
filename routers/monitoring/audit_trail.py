from fastapi import APIRouter, Query, Depends
from typing import List, Optional, Literal
from config import require_credentials
from models import Alert
from utils import paginated_fetch, compute_time_window
from services.central_service import get_conn

AUDIT_LIMIT = 200  # Default limit for alerts if not specified in query parameters
router = APIRouter(
    prefix="/audit", tags=["audit"], dependencies=[Depends(require_credentials)]
)


@router.get("", operation_id="get_audit_trail")
async def get_audit_trail(
    time_range: Literal[
        "last_1h", "last_6h", "last_24h", "last_7d", "last_30d", "today", "yesterday"
    ] = Query("last_1h", description="Predefined time window"),
    source: Optional[Literal["system", "user"]] = Query(
        None,
        description=(
            "Filter audit events by origin. "
            "'system' returns only Central system-generated events. "
            "'user' returns only user-triggered events, excluding system events."
        ),
    ),
    username: Optional[str] = Query(
        None,
        max_length=128,
        description=(
            "Email address of a specific user to filter audit events for. "
            "When provided, returns only events associated with that user's email address."
        ),
    ),
):
    """
    Get audit trail of Central system & user actions within a specified time range.

    Use the time_range parameter to specify the desired time window for the audit trail.
    Use the source parameter to filter by event origin:
      - 'system': returns only Central system-generated events.
      - 'user': returns only user-triggered events (system events are excluded).
    Optionally, specify a username (email address) to narrow results to a specific
    user's actions. When username is provided, source is ignored and only events
    matching that user's email are returned.
    """
    start_dt, end_dt = compute_time_window(time_range)
    print(f"Computed time window - Start: {start_dt}, End: {end_dt}")
    start_query_time = int(start_dt.timestamp() * 1000)
    end_query_time = int(end_dt.timestamp() * 1000)
    print(f"Computed time window - Start: {start_query_time}, End: {end_query_time}")
    query_params = {
        "start-at": start_query_time,
        "end-at": end_query_time,
    }

    if username:
        query_params["filter"] = f'source eq "{username}"'
    elif source == "system":
        query_params["filter"] = 'source eq "System"'

    # Fetch all audit events within the specified time range
    audit_trail = paginated_fetch(
        central_conn=get_conn(),
        api_path="network-services/v1alpha1/audits",
        additional_params=query_params,
        limit=AUDIT_LIMIT,
        use_cursor=False,
        offset_start=1,
        items_key="audits",
    )

    if not username and source == "user":
        audit_trail = [a for a in audit_trail if a.get("source") != "System"]

    return audit_trail


# @router.get("/users", operation_id="get_user_audit_trail")
# async def get_user_audit_trail(
#     time_range: Literal[
#         "last_1h", "last_6h", "last_24h", "last_7d", "last_30d", "today", "yesterday"
#     ] = Query("last_1h", description="Predefined time window"),
#     user_email: Optional[str] = Query(
#         None, description="Email of the user to filter audit events for"
#     ),
# ):
#     """Get audit trail of user actions within a specified time range, with optional filtering by user email. Use this endpoint to focus specifically on user-triggered events, excluding system-generated events. The user_email parameter allows you to filter the audit trail to show only events associated with a particular user's email address. If user_email is not provided, the endpoint will return all user-triggered events while excluding system events.

#     Args:
#         time_range (Literal[ "last_1h", "last_6h", "last_24h", "last_7d", "last_30d", "today", "yesterday" ], optional): Predefined time window for the audit trail. Defaults to "last_1h".
#         user_email (Optional[str], optional): Email of the user to filter audit events for. Defaults to None.
#     """
#     start_dt, end_dt = compute_time_window(time_range)

#     start_query_time = int(start_dt.timestamp() * 1000)
#     end_query_time = int(end_dt.timestamp() * 1000)
#     print(f"Computed time window - Start: {start_query_time}, End: {end_query_time}")
#     query_params = {
#         "start-at": start_query_time,
#         "end-at": end_query_time,
#     }

#     if user_email:
#         query_params["filter"] = f'source eq "{user_email}"'
#     # Fetch all audit events within the specified time range
#     audit_trail = paginated_fetch(
#         central_conn=get_conn(),
#         api_path="network-services/v1alpha1/audits",
#         additional_params=query_params,
#         limit=AUDIT_LIMIT,
#         use_cursor=False,
#         offset_start=1,
#         items_key="audits",
#     )
#     if not user_email:
#         user_audit_trails = []
#         for audit in audit_trail:
#             if audit.get("source") != "System":
#                 user_audit_trails.append(audit)
#         audit_trail = user_audit_trails
#     return audit_trail
