from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from models import Client
from utils import paginated_fetch, clean_client_data
from services.central_service import get_conn
from config import require_credentials


router = APIRouter(
    prefix="/clients", tags=["clients"], dependencies=[Depends(require_credentials)]
)


@router.get("", operation_id="get_all_clients", response_model=List[Client])
async def get_all_clients() -> List[Client]:
    """
    Purpose: Return a list of ALL clients from Central. WARNING: This is an EXPENSIVE operation.
        DO NOT call this for general network health or overview questions - use filter_clients instead.
        Only call this when the user EXPLICITLY requests a complete client list or for troubleshooting specific client details where a complete list is necessary.
        For targeted queries (by site, health, status, type), use filter_clients instead.

    ## Responses:

    **200**: Successful Response
    Returns a list of clients with the following attributes:
        - **mac** (string): Unique MAC address identifier for the client
        - **name** (string, optional): Display name of the client
        - **ipv4** (string, optional): IPv4 address assigned to the client
        - **ipv6** (string, optional): IPv6 address assigned to the client
        - **hostname** (string, optional): Hostname of the client device

        - **type** (string, optional): Client connection type (e.g., "Wireless", "Wired")
        - **vendor** (string, optional): Device vendor identification
        - **manufacturer** (string, optional): Device manufacturer
        - **category** (string, optional): Device category (e.g., "Computing Systems")
        - **function** (string, optional): Device function (e.g., "Operating System")
        - **model_os** (string, optional): Operating system model
        - **capabilities** (string, optional): Device capabilities

        - **status** (string, optional): Connection status (e.g., "Connected", "Failed")
        - **status_reason** (string, optional): Detailed status reason (e.g., "CLIENT_FAILURE_REASON_DHCP_DISCOVER_TIMEOUT")
        - **health** (string, optional): Client health score (e.g., "Good", "Fair", "Poor")

        - **connected_device_type** (string, optional): Type of device client is connected to (e.g., "AP", "SWITCH")
        - **connected_device_serial** (string, optional): Serial number of connected device
        - **connected_to** (string, optional): Name of the device client is connected to
        - **connected_since** (string, optional): Duration of connection
        - **last_seen_at** (string, optional): Timestamp of last client activity
        - **port** (string, optional): Port number for wired clients

        - **network** (string, optional): Network name/SSID
        - **vlan_id** (string, optional): VLAN identifier
        - **tunnel** (string, optional): Tunnel type
        - **tunnel_id** (string, optional): Tunnel identifier

        - **ssid** (string, optional): Wireless network SSID
        - **wireless_band** (string, optional): Wireless frequency band (e.g., "5 GHz", "2.4 GHz")
        - **wireless_channel** (string, optional): Wireless channel number
        - **wireless_security** (string, optional): Wireless security type
        - **key_management** (string, optional): Key management protocol
        - **vap_bssid** (string, optional): Virtual AP BSSID
        - **radio_mac** (string, optional): Radio MAC address

        - **user_name** (string, optional): Authenticated username
        - **authentication** (string, optional): Authentication method

        - **site_id** (string, optional): ID of the site where client is located
        - **site_name** (string, optional): Name of the site where client is located

        - **role** (string, optional): Client role assignment
        - **tags** (string, optional): Associated tags

    **Example Response:**
      ```json
      [
        {
            "mac": "00:11:11:00:00:7a",
            "name": "00:11:11:00:00:7a",
            "ipv4": "",
            "ipv6": "",
            "hostname": "",
            "type": "Wireless",
            "vendor": "Debian/Ubuntu/Knoppix",
            "manufacturer": "Intel Corporation",
            "category": "Computing Systems",
            "function": "Operating System",
            "model_os": "Debian/Ubuntu/Knoppix Linux",
            "capabilities": "unspecified",
            "status": "Failed",
            "status_reason": "CLIENT_FAILURE_REASON_DHCP_DISCOVER_TIMEOUT",
            "health": "Poor",
            "connected_device_type": "AP",
            "connected_device_serial": "CNP7KZ24YT",
            "connected_to": "BO-MIA-AP04",
            "connected_since": "0",
            "last_seen_at": "2026-01-28T10:31:27.600Z",
            "port": null,
            "network": "MIA-1X",
            "vlan_id": "0",
            "tunnel": "None",
            "tunnel_id": null,
            "ssid": null,
            "wireless_band": "5 GHz",
            "wireless_channel": null,
            "wireless_security": "Unspecified",
            "key_management": "Unspecified",
            "vap_bssid": "74:9e:75:22:21:90",
            "radio_mac": "74:9e:75:22:21:90",
            "user_name": "",
            "authentication": "",
            "site_id": "3917546799",
            "site_name": "Miami (MIA) - Branch",
            "role": null,
            "tags": ""
        }
      ]
      ```
    """
    all_clients = paginated_fetch(get_conn(), "network-monitoring/v1/clients", 1000)

    cleaned_clients = clean_client_data(all_clients)

    return cleaned_clients


@router.get("/filter", operation_id="filter_clients")
async def filter_clients(
    site_id: Optional[str] = Query(
        None,
        description="The ID of the site from which the clients are to be retrieved",
    ),
    site_name: Optional[str] = Query(
        None,
        description="The name of the site from which the clients are to be retrieved",
    ),
    serial_number: Optional[str] = Query(
        None, description="Specifies the device identifier (device serial number)"
    ),
    start_query_time: Optional[str] = Query(
        None,
        max_length=13,
        description="Start timestamp in epoch milliseconds. Defaults to last 3hrs. Can be set up to 30 days in the past",
    ),
    end_query_time: Optional[str] = Query(
        None,
        max_length=13,
        description="End timestamp in epoch milliseconds. Will be set to current timestamp even if provided",
    ),
    health: Optional[str] = Query(
        None,
        description="Filter by client health. Supported values: Good, Fair, Poor. Use comma-separated for multiple values",
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by client status. Supported values: Connected, Failed, Connecting, Disconnected, Blocked, Unknown. Use comma-separated for multiple values",
    ),
    type: Optional[str] = Query(
        None,
        description="Filter by client type. Supported values: Wired, Wireless. Use comma-separated for multiple values",
    ),
    network: Optional[str] = Query(
        None,
        description="Filter by network name/SSID. Use comma-separated for multiple values",
    ),
    vlan_id: Optional[str] = Query(
        None, description="Filter by VLAN ID. Use comma-separated for multiple values"
    ),
    tunnel: Optional[str] = Query(
        None,
        description="Filter by tunnel type. Supported values: Port-based, User-based, Overlay. Use comma-separated for multiple values",
    ),
    role: Optional[str] = Query(
        None,
        description="Filter by client role. Use comma-separated for multiple values",
    ),
    sort: Optional[str] = Query(
        None,
        max_length=256,
        description="Sort field followed by ASC or DESC. Supported fields: name, health, status, statusReason, type, mac, ipv4, ipv6, connectedDeviceSerial, connectedTo, lastSeenAt, port, role, network, vlanId, tunnel, tunnelId, connectedSince",
    ),
    limit: Optional[int] = Query(
        100, ge=1, le=100, description="Maximum number of clients to retrieve (1-100)"
    ),
) -> List[Client]:
    """
    Purpose: Return a filtered list of clients from Central based on various criteria using OData v4.0 filter syntax

    ## Query Parameters:

    - **site_id** (string, optional): Filter by site ID
    - **site_name** (string, optional): Filter by site name
    - **serial_number** (string, optional): Filter by device serial number
    - **start_query_time** (string, optional): Start timestamp in epoch milliseconds (max length: 13)
    - **end_query_time** (string, optional): End timestamp in epoch milliseconds (max length: 13)
    - **health** (string, optional): Filter by health (Good, Fair, Poor) - comma-separated for multiple
    - **status** (string, optional): Filter by status (Connected, Failed, Connecting, Disconnected, Blocked, Unknown) - comma-separated for multiple
    - **type** (string, optional): Filter by type (Wired, Wireless) - comma-separated for multiple
    - **network** (string, optional): Filter by network name/SSID - comma-separated for multiple
    - **vlan_id** (string, optional): Filter by VLAN ID - comma-separated for multiple
    - **tunnel** (string, optional): Filter by tunnel type (Port-based, User-based, Overlay) - comma-separated for multiple
    - **role** (string, optional): Filter by client role - comma-separated for multiple
    - **sort** (string, optional): Sort expression (e.g., 'name ASC', 'health DESC')
    - **limit** (integer, optional): Maximum results to return (1-1000, default: 100)

    ## Responses:

    **200**: Successful Response
    Returns a list of clients matching the filter criteria with the same attributes as the get_all_clients endpoint:
        - **mac** (string): Unique MAC address identifier
        - **name** (string, optional): Display name of the client
        - **ipv4/ipv6** (string, optional): IP addresses
        - **hostname** (string, optional): Hostname of the client device
        - **type** (string, optional): Client connection type (Wireless/Wired)
        - **vendor/manufacturer** (string, optional): Device vendor/manufacturer info
        - **status** (string, optional): Connection status (Connected/Failed/Disconnected)
        - **health** (string, optional): Health score (Good/Fair/Poor)
        - **connected_device_type/connected_device_serial/connected_to** (string, optional): Connection details
        - **network/ssid/vlan_id** (string, optional): Network information
        - **site_id/site_name** (string, optional): Site location
        - Plus all other client attributes

    ## Example Request:
    ```
    GET /clients/filter?status=Connected&health=Good&type=Wireless&limit=50
    ```

    ## Example Response:
    ```json
    [
      {
        "mac": "00:11:11:00:00:7a",
        "name": "00:11:11:00:00:7a",
        "ipv4": "",
        "ipv6": "",
        "hostname": "",
        "type": "Wireless",
        "vendor": "Debian/Ubuntu/Knoppix",
        "manufacturer": "Intel Corporation",
        "category": "Computing Systems",
        "function": "Operating System",
        "model_os": "Debian/Ubuntu/Knoppix Linux",
        "capabilities": "unspecified",
        "status": "Failed",
        "status_reason": "CLIENT_FAILURE_REASON_DHCP_DISCOVER_TIMEOUT",
        "health": "Poor",
        "connected_device_type": "AP",
        "connected_device_serial": "CNP7KZ24YT",
        "connected_to": "BO-MIA-AP04",
        "connected_since": "0",
        "last_seen_at": "2026-01-28T10:31:27.600Z",
        "port": null,
        "network": "MIA-1X",
        "vlan_id": "0",
        "tunnel": "None",
        "tunnel_id": null,
        "ssid": null,
        "wireless_band": "5 GHz",
        "wireless_channel": null,
        "wireless_security": "Unspecified",
        "key_management": "Unspecified",
        "vap_bssid": "74:9e:75:22:21:90",
        "radio_mac": "74:9e:75:22:21:90",
        "user_name": "",
        "authentication": "",
        "site_id": "3917546799",
        "site_name": "Miami (MIA) - Branch",
        "role": null,
        "tags": ""
      }
    ]
    ```
    """
    # Build OData filter string
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

    if health:
        add_filter("health", health)
    if status:
        add_filter("status", status)
    if type:
        add_filter("type", type)
    if network:
        add_filter("network", network)
    if vlan_id:
        add_filter("vlanId", vlan_id)
    if tunnel:
        add_filter("tunnel", tunnel)
    if role:
        add_filter("role", role)

    # Build query parameters
    query_params = {}

    if filter_parts:
        query_params["filter"] = " and ".join(filter_parts)
    if site_id:
        query_params["site-id"] = site_id
    if site_name:
        query_params["site-name"] = site_name
    if serial_number:
        query_params["serial-number"] = serial_number
    if start_query_time:
        query_params["start-query-time"] = start_query_time
    if end_query_time:
        query_params["end-query-time"] = end_query_time
    if sort:
        query_params["sort"] = sort

    # Fetch filtered clients from API
    clients = paginated_fetch(
        get_conn(),
        "network-monitoring/v1alpha1/clients",
        limit,
        additional_params=query_params,
        use_cursor=True,
    )

    cleaned_clients = clean_client_data(clients)

    return cleaned_clients
