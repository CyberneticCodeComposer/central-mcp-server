from fastmcp import Context
from typing import List, Literal, Optional
from models import Alert
from utils import paginated_fetch, build_odata_filter, FilterField, clean_alert_data
from tools import READ_ONLY

ALERT_LIMIT = 100

ALERT_FILTER_FIELDS: dict[str, FilterField] = {
    "status": FilterField("status"),
    "device_type": FilterField("deviceType"),
    "category": FilterField("category"),
    "site_id": FilterField("siteId"),
}


def register(mcp):

    @mcp.tool(annotations=READ_ONLY)
    async def central_get_alerts(
        ctx: Context,
        site_id: str,
        status: Optional[Literal["Active", "Cleared", "Deferred"]] = "Active",
        device_type: Optional[
            Literal["Access Point", "Gateway", "Switch", "Bridge"]
        ] = None,
        category: Optional[
            Literal[
                "Clients",
                "System",
                "LAN",
                "WLAN",
                "WAN",
                "Cluster",
                "Routing",
                "Security",
            ]
        ] = None,
        sort: str = "createdAt desc",
    ) -> List[Alert] | str:
        """
        Returns a filtered list of alerts for a specific site. Call central_get_site_name_id_mapping
        first to obtain site_id values, then use this to drill into active issues by device
        type or category. Prioritize results by severity (Critical > High > Medium > Low)
        and recency (createdAt).

        If no alerts match the criteria, returns a message indicating so.

        Parameters:
            - site_id: Site identifier from central_get_site_name_id_mapping (required).
            - status: "Active" (default) for unresolved alerts, "Cleared" for resolved ones.
            - device_type: Narrow to a device class — "Access Point", "Gateway", "Switch", or "Bridge".
            - category: Narrow to an alert domain — "Clients", "System", "LAN", "WLAN", "WAN",
              "Cluster", "Routing", or "Security".
            - sort: Sort expression (default "createdAt desc"). Examples: "createdAt asc",
              "severity desc".

        Note: Each alert includes summary, name, category, severity, priority, status,
        deviceType, createdAt, updatedAt, updatedBy, and clearedReason.
        """
        raw_pairs = [
            ("status", status),
            ("device_type", device_type),
            ("category", category),
            ("site_id", site_id),
        ]
        pairs = [(ALERT_FILTER_FIELDS[k], v) for k, v in raw_pairs if v is not None]

        query_params = {"sort": sort}
        odata = build_odata_filter(pairs)
        if odata:
            query_params["filter"] = odata

        alerts = paginated_fetch(
            ctx.lifespan_context["conn"],
            "network-notifications/v1/alerts",
            ALERT_LIMIT,
            additional_params=query_params,
            use_cursor=True,
        )
        if not alerts:
            return "No alerts found matching criteria"
        return clean_alert_data(alerts)
