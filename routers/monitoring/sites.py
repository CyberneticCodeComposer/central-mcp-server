from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from models import SiteData
from utils import fetch_site_data_parallel
from services.central_service import get_conn
from config import require_credentials


router = APIRouter(
    prefix="/sites", tags=["sites"], dependencies=[Depends(require_credentials)]
)


@router.get("", operation_id="get_sites", response_model=List[SiteData])
async def get_sites(
    site_names: List[str] = Query(
        default=[],
        description="Optional list of site names to filter results. Matching is case-insensitive and supports partial (substring) matches. Pass multiple values as repeated query parameters: ?site_names=Miami&site_names=Mumbai. Omit to return all sites.",
    ),
) -> List[SiteData]:
    """
    Purpose: Returns detailed metrics for one or more sites. Prefer calling this with a site_names filter
        targeting only the sites you care about — do NOT call without a filter unless the user explicitly
        requests data for all sites, as returning all sites is expensive and consumes significant context.
        **Recommended workflow:** Call `get_site_name_id_mapping` (get_site_summary) first to get a
        lightweight overview of all sites (names, IDs, health scores). Use the health scores and alert
        counts from that response to decide which sites warrant further investigation, then call this
        endpoint with those specific site names as filters.
        If site_names is provided, results are filtered to sites whose names match any entry in the list.
        Matching is case-insensitive and supports partial (substring) matches, so "miami" will match
        "Miami (MIA) - Branch". If omitted, all sites are returned (use sparingly).

    ## Parameters:
        - **site_names** (list of strings, optional): One or more site name fragments to filter by.
          Each value is matched case-insensitively as a substring against site names.
          Pass multiple values as repeated query params: `?site_names=Miami&site_names=Mumbai`.
          **Tip:** If you are unsure of the exact site name, call `get_site_name_id_mapping` first
          to retrieve the full list of site names and their IDs, then pass the correct name here.
    ## Responses:

    **200**: Successful Response
    Returns a list of sites with the following attributes:
        - **site_id** (string): Unique identifier for the site in Central. This ID is used for referencing the site in API calls.
        - **name** (string): Display name of the site
        - **address** (object): Physical address information of the site
        - **location** (object): Geographic coordinates of the site
        - **metrics** (object): Site performance metrics including:
            - **health** (object): Overall health status and scores. This includes percentage-based distrubtion plus a single summary score.
                - poor (int): Percentage of poor health
                - fair (int): Percentage of fair health
                - good (int): Percentage of good health
                - summary (int): Overall health score calculated as a weighted average (Good=1, Fair=0.5, Poor=0)
            - **devices** (object): Device statistics of the site
               - Summary (object, required): Aggregate device counts for the site.
                        - Poor (int): Number of devices in poor state
                        - Fair (int): Number of devices in fair state
                        - Good (int): Number of devices in good state
                        - Total (int): Total number of devices
               - Details (object, optional): Per-device-type counts. Keys are device-type names (e.g., "Access Points", "Switches", "Gateways", "Bridges").
                   Each value is:
                       - Poor (int)
                       - Fair (int)
                       - Good (int)
            - **clients** (object): Client statistics of the site
               - Summary (object, required): Aggregate client counts for the site.
                    - Poor (int): Count of clients in poor status
                    - Fair (int): Count of clients in fair status
                    - Good (int): Count of clients in good status
                    - Total (int): Total count of clients
               - Details (object, optional): Per-client-medium counts. Keys are mediums like "Wired" and "Wireless".
                   Each value is:
                       - Poor (int)
                       - Fair (int)
                       - Good (int)
            - **alerts** (object): Alert counts.
                - Critical (int): Count of critical alerts
                - Total (int): Total count of alerts
    **Example Response:**
      ```json
      [
        {
            "site_id": "12132434322",
            "name": "site-12-dec",
            "address": {
                "zipCode": "560048",
                "address": "Bangalore 560048",
                "city": "Bangalore",
                "state": "Karnataka",
                "country": "India"
            },
            "location": {
                "lat": 12.9853591,
                "lng": 77.7081261
            },
            "metrics": {
                "health": {
                    "Poor": 0,
                    "Fair": 0,
                    "Good": 100,
                    "Summary": 100
                },
                "devices": {
                    "Summary": {
                        "Poor": 3,
                        "Fair": 0,
                        "Good": 0,
                        "Total": 3
                    },
                "clients": {
                    "Summary": {
                        "Poor": 0,
                        "Fair": 0,
                        "Good": 0,
                        "Total": 0
                    },
                "alerts": {
                    "Critical": 3,
                    "Total": 3
                }
            }
        }
    ]
    """
    sites_data = fetch_site_data_parallel(get_conn())
    if site_names:
        filtered_sites = []
        for site in sites_data:
            filtered_sites.append(sites_data[site])
        return filtered_sites
    return list(sites_data.values())


@router.get("/summary", operation_id="get_site_summary")
async def get_site_name_id_mapping() -> dict:
    """
    Purpose: Returns a lightweight mapping of site names to their IDs and health scores.
        Use this endpoint to look up the exact site name and site_id before calling other endpoints.
        This is especially useful when the user provides a partial or ambiguous site name — verify
        the correct name here, then pass it to `get_sites` (site_names filter) or other endpoints
        that require site_id. The health score can also help identify sites with issues before drilling down
        further.

    ## Responses:

    **200**: Successful Response
    Returns a dictionary where each key is the site name (string) and the value is an object with:
        - **site_id** (string): Unique identifier for the site, used in other API calls.
        - **health** (int): Overall health score of the site (weighted average: Good=1, Fair=0.5, Poor=0)

    **Example Response:**
    ```json
    {
        "Mumbai (BOM) - Branch": {
            "site_id": "4796412359",
            "health": 80
        },
        "Miami (MIA) - Branch": {
            "site_id": "9823471029",
            "health": 100
        }
    }
    ```
    """
    all_sites = fetch_site_data_parallel(get_conn())
    mapping = {}
    for site_name in all_sites:
        mapping[site_name] = {
            "site_id": all_sites[site_name].site_id,
            "health": all_sites[site_name].metrics.health["Summary"],
        }

    return mapping
