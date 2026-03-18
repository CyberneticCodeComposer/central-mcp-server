from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from routers.monitoring import (
    sites_router,
    devices_router,
    clients_router,
    alerts_router,
    application_visibility_router,
    audit_trail_router,
    events_router,
)

app = FastAPI()

# Include routers
app.include_router(sites_router)
app.include_router(devices_router)
app.include_router(clients_router)
app.include_router(alerts_router)
app.include_router(application_visibility_router)
app.include_router(audit_trail_router)
app.include_router(events_router)


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to the Central MCP API. Visit /docs for API documentation."
    }


if __name__ == "__main__":
    try:
        # Credentials are loaded from .env.local file via config.py
        mcp = FastApiMCP(
            app,
            name="Central MCP",
            description="""MCP server for HPE Aruba Central network monitoring and management.
IMPORTANT USAGE GUIDELINES:
- ALWAYS start with get_site_summary (get_site_name_id_mapping) to get a lightweight overview of all sites — names, site_ids, and health scores. Use this to assess the network state and identify which sites need attention before fetching detailed data.
- If user asks for network summary, run get_sites without a filter to return all sites. For each site, include the health score, device, client & alert count in the response to help users quickly identify which sites may have issues.
- For overall summaries, first fetch sites with get_sites using a site_names filter to drill into specific sites of interest (e.g., those with poor/fair health or high alert counts). Avoid calling get_sites without a filter unless the user explicitly requests data for all sites.
- ONLY call get_sites with a site_names filter after reviewing get_site_summary results. Pass only the specific site names you need (e.g., those with low health scores or active issues). Do NOT call get_sites without a filter unless the user explicitly requests full data for all sites.
- For any site-specific question, use get_sites with the site name to get detailed information about that site, including health metrics, device/client/alert summaries, and location metadata.
- get_all_devices and get_all_clients are EXPENSIVE operations that fetch all records. Only call these when the user EXPLICITLY requests a full device list or client list.
- For targeted queries, prefer filter_devices, filter_alerts, filter_clients which support filtering by site, status, health, and other criteria.
- You can provide recommendations when you use filter_alerts to identify specific issues, but ALWAYS base your recommendations strictly on the API response data. DO NOT make assumptions or provide recommendations that are not directly supported by the API response.


Recommended workflow:
1. Call get_site_summary first — it returns a lightweight map of all site names, site_ids, and health scores with minimal context cost. Use health scores to identify which sites need attention.
2. Call get_sites with a site_names filter for only the sites you need to drill into (e.g., poor/fair health, high alert counts). Avoid calling get_sites without a filter unless the user explicitly asks for all sites.
3. Use filter_devices, filter_alerts, filter_clients for specific queries
4. Only use get_all_devices/get_all_clients when explicitly requested""",
            describe_full_response_schema=True,
            include_operations=[
                "get_sites",
                "get_site_summary",
                "filter_devices",
                "filter_clients",
                "filter_alerts",
                "get_events",
                "get_audit_trail",
                # "get_all_devices",
                # "get_all_clients",
            ],
        )
        mcp.mount_http()
        import uvicorn

        print("Starting server on http://0.0.0.0:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except Exception as e:
        print(f"Error starting server: {e}")
        raise
