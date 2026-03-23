from fastmcp import Context
from typing import Literal, Optional
from models import Event, EventFilters
from utils import (
    clean_event_filters,
    compute_time_window,
    paginated_fetch,
    retry_central_command,
)
from tools import READ_ONLY

EVENT_LIMIT = 100

CONTEXT_TYPE = Literal[
    "SITE",
    "ACCESS_POINT",
    "SWITCH",
    "GATEWAY",
    "WIRELESS_CLIENT",
    "WIRED_CLIENT",
    "BRIDGE",
]

TIME_RANGE = Literal[
    "last_1h", "last_6h", "last_24h", "last_7d", "last_30d", "today", "yesterday"
]


def _resolve_time_window(
    time_range: str,
    start_time: Optional[str],
    end_time: Optional[str],
) -> tuple[str, str]:
    """Return (start_at, end_at) as RFC 3339 strings.

    If both start_time and end_time are provided, use them as-is.
    Otherwise compute the window from the time_range preset.
    """
    if start_time and end_time:
        return start_time, end_time
    start_dt, end_dt = compute_time_window(time_range)
    fmt = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
    return fmt(start_dt), fmt(end_dt)


def register(mcp):

    @mcp.tool(annotations=READ_ONLY)
    async def central_get_events(
        ctx: Context,
        context_type: CONTEXT_TYPE,
        context_identifier: str,
        site_id: str,
        time_range: TIME_RANGE = "last_1h",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[Event] | str:
        """
        Retrieve events for a given context (site, device, or client) within a specified time range.

        Use central_get_events_count first to understand what event types and volumes exist before
        fetching full event records.

        Parameters:
        - context_type: Type of context entity — what context_identifier refers to. Allowed values:
          SITE, ACCESS_POINT, SWITCH, GATEWAY, WIRELESS_CLIENT, WIRED_CLIENT, BRIDGE.
        - context_identifier: Identifier for the context — site ID if context_type is SITE, device
          serial number if context_type is a device type, or client MAC address if a client type.
        - site_id: Site ID to scope events. Required even when context_type is not SITE.
        - time_range: Predefined time window. Allowed values: last_1h, last_6h, last_24h, last_7d,
          last_30d, today, yesterday. Ignored if both start_time and end_time are provided.
        - start_time: Start of the time window in RFC 3339 format (e.g. "2026-03-21T00:00:00.000Z").
          Overrides time_range when combined with end_time.
        - end_time: End of the time window in RFC 3339 format (e.g. "2026-03-21T23:59:59.999Z").
          Overrides time_range when combined with start_time.
        - search: Search events by name, serial number, host name, or MAC address. Restricted to
          metadata fields only; full-text search is not supported.
        """
        start_at, end_at = _resolve_time_window(time_range, start_time, end_time)

        query_params = {
            "context-type": context_type,
            "context-identifier": context_identifier,
            "start-at": start_at,
            "end-at": end_at,
            "site-id": site_id,
        }
        if search:
            query_params["search"] = search

        try:
            events = paginated_fetch(
                ctx.lifespan_context["conn"],
                "network-troubleshooting/v1/events",
                EVENT_LIMIT,
                additional_params=query_params,
                use_cursor=True,
                items_key="events",
            )
        except Exception as e:
            return f"Error fetching events: {e}"
        return [Event(**event) for event in events]

    @mcp.tool(annotations=READ_ONLY)
    async def central_get_events_count(
        ctx: Context,
        context_type: CONTEXT_TYPE,
        context_identifier: str,
        site_id: str,
        time_range: TIME_RANGE = "last_1h",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> EventFilters:
        """
        Return a breakdown of event counts for a context without fetching full event details.

        Use this before central_get_events to understand what types and volumes of events exist,
        avoiding the overhead of retrieving all event records.

        Parameters:
        - context_type: Type of context entity. Allowed values: SITE, ACCESS_POINT, SWITCH,
          GATEWAY, WIRELESS_CLIENT, WIRED_CLIENT, BRIDGE.
        - context_identifier: Identifier for the context — site ID, device serial number, or
          client MAC address.
        - site_id: Site ID to scope events to a specific site.
        - time_range: Predefined time window. Allowed values: last_1h, last_6h, last_24h, last_7d,
          last_30d, today, yesterday. Ignored if both start_time and end_time are provided.
        - start_time: Start of the time window in RFC 3339 format (e.g. "2026-03-21T00:00:00.000Z").
          Overrides time_range when combined with end_time.
        - end_time: End of the time window in RFC 3339 format (e.g. "2026-03-21T23:59:59.999Z").
          Overrides time_range when combined with start_time.

        Returns an EventFilters object: total event count plus breakdowns by event name, source
        type, and category.
        """
        start_at, end_at = _resolve_time_window(time_range, start_time, end_time)

        response = retry_central_command(
            ctx.lifespan_context["conn"],
            api_method="GET",
            api_path="network-troubleshooting/v1/event-filters",
            api_params={
                "context-type": context_type,
                "context-identifier": context_identifier,
                "start-at": start_at,
                "end-at": end_at,
                "site-id": site_id,
            },
        )
        return clean_event_filters(response["msg"])
