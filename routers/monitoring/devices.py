from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from models import Device
from utils import paginated_fetch, clean_device_duplicates
from services.central_service import get_conn
from config import require_credentials


router = APIRouter(
    prefix="/devices", tags=["devices"], dependencies=[Depends(require_credentials)]
)


@router.get("", operation_id="get_all_devices")
async def get_all_devices() -> List[Device]:
    """
    Purpose: Return a list of ALL devices from Central. WARNING: This is an EXPENSIVE operation.
        DO NOT call this for general network health or overview questions - use get_sites instead.
        Only call this when the user EXPLICITLY requests a complete device list or inventory.
        For targeted queries (by site, type, model, status), use filter_devices instead.

    ## Responses:

    **200**: Successful Response
    Returns a list of devices with the following attributes:
        - **serial_number** (string): Unique serial number identifier for the device. This is used to identify the device on Central. This is the most reliable way to reference a device.
        - **mac_address** (string): MAC address of the device
        - **device_type** (string): Type of device (e.g., "ACCESS_POINT", "SWITCH", "GATEWAY")
        - **model** (string): Device model number.
        - **part_number** (string): Manufacturer part number
        - **name** (string): Display name of the device. This is configurable on Central and can be changed by users.
        - **function** (string): Device function classification. This defines the role of the device in the network.
        - **status** (string): Current operational status (e.g., "ONLINE", "OFFLINE").
        - **is_provisioned** (bool): Provisioning status - returns True or False. Provisioning status indicates whether the device is configured and provisioned to new Central. If this is false, the device is not yet provisioned & not sending monitoring data to new Central.
        - **scope_id** (string): Scope identifier for the device. This needed for any configuration related actions with the device.
        - **role** (string): Device role in the network
        - **deployment** (string): Deployment mode (e.g., "Standalone", "Stack")
        - **tier** (string, optional): Device License tier classification (e.g., "ADVANCED_AP"). This provides details on which type of Central subscription is used to subscribe the device.
        - **firmware_version** (string): Current firmware version installed on the device
        - **site_id** (string): ID of the site where device is located
        - **site_name** (string): Name of the site where device is located
        - **device_group_name** (string, optional): Name of the device group
        - **ipv4** (string, optional): IPv4 address of the device

    **Example Response:**
      ```json
      [
        {
            "serial_number": "USTWM5206L",
            "mac_address": "ec:1b:5f:c9:92:f3",
            "device_type": "ACCESS_POINT",
            "model": "AP-735-RWF1",
            "part_number": "S1G47A",
            "name": "IMF-BLR-CP-AP02",
            "function": "-",
            "status": "OFFLINE",
            "is_provisioned": false,
            "role": "-",
            "deployment": "Standalone",
            "tier": "ADVANCED_AP",
            "firmware_version": "10.7.2.1_93186",
            "site_id": "48424357225234432",
            "site_name": "IMF-Bengaluru-Campus",
            "device_group_name": null,
            "scope_id": "48407759959924736",
            "ipv4": "172.16.10.55",
            "stack_id": null,
        }
      ]
      ```
    """
    all_devices = paginated_fetch(
        get_conn(), "network-monitoring/v1alpha1/device-inventory", 1000
    )

    cleaned_devices = clean_device_duplicates(all_devices)

    return cleaned_devices


@router.get("/filter", operation_id="filter_devices")
async def filter_devices(
    site_id: Optional[str] = Query(
        None, description="Filter by site ID (exact match or comma-separated list)"
    ),
    device_type: Optional[str] = Query(
        None,
        description="Filter by device type (ACCESS_POINT, SWITCH, GATEWAY) - exact match or comma-separated list",
    ),
    device_name: Optional[str] = Query(
        None, description="Filter by device name (exact match or comma-separated list)"
    ),
    serial_number: Optional[str] = Query(
        None,
        description="Filter by serial number (exact match or comma-separated list)",
    ),
    model: Optional[str] = Query(
        None, description="Filter by device model (exact match or comma-separated list)"
    ),
    device_function: Optional[str] = Query(
        None,
        description="Filter by device function (exact match or comma-separated list)",
    ),
    is_provisioned: Optional[bool] = Query(
        None, description="Filter by provisioning status (true/false)"
    ),
    site_assigned: Optional[str] = Query(
        None, description="Filter by site assignment status (ASSIGNED or UNASSIGNED)"
    ),
    search: Optional[str] = Query(
        None,
        description="Search term to filter devices. Searches: deviceName, persona, model, serialNumber, macAddress, ipv4, softwareVersion",
    ),
    sort: Optional[str] = Query(
        None,
        description="Comma-separated sort expressions (e.g., 'deviceName asc, model desc'). Supported: siteId, model, siteName, serialNumber, macAddress, deviceType, ipv4, deviceGroupName, deviceFunction, deviceName",
    ),
) -> List[Device]:
    """
    Purpose: Return a filtered list of devices from Central based on various criteria using OData v4.0 filter syntax. This tool is useful for narrowing down large device inventories to specific subsets for monitoring and management.
    It's highly recommended to call get_site_name_id_mapping first to obtain site_id for filtering. Use this endpoint for targeted queries by site, type, model, status, etc. For general inventory requests, use get_all_devices.

    ## Query Parameters:

    - **site_id** (string, optional): Filter by site ID. Use comma-separated values for multiple IDs.
    - **device_type** (string, optional): Filter by device type (ACCESS_POINT, SWITCH, GATEWAY).
    - **device_name** (string, optional): Filter by device name.
    - **serial_number** (string, optional): Filter by serial number.
    - **model** (string, optional): Filter by device model.
    - **device_function** (string, optional): Filter by device function classification.
    - **is_provisioned** (bool, optional): Filter by provisioning status (true/false).
    - **site_assigned** (string, optional): Filter by site assignment status (ASSIGNED or UNASSIGNED).
    - **search** (string, optional): Search term to filter devices. Free-text search across deviceName, persona, model, serialNumber, macAddress, ipv4, softwareVersion.
    - **sort** (string, optional): Comma-separated sort expressions (e.g., 'deviceName asc, model desc')

    ## Responses:

    **200**: Successful Response
    Returns a list of devices with the following attributes:
        - **serial_number** (string): Unique serial number identifier for the device. This is used to identify the device on Central. This is the most reliable way to reference a device.
        - **mac_address** (string): MAC address of the device
        - **device_type** (string): Type of device (e.g., "ACCESS_POINT", "SWITCH", "GATEWAY")
        - **model** (string): Device model number.
        - **part_number** (string): Manufacturer part number
        - **name** (string): Display name of the device. This is configurable on Central and can be changed by users.
        - **function** (string): Device function classification. This defines the role of the device in the network.
        - **status** (string): Current operational status (e.g., "ONLINE", "OFFLINE").
        - **is_provisioned** (bool): Provisioning status - returns True or False. Provisioning status indicates whether the device is configured and provisioned to new Central. If this is false, the device is not yet provisioned & not sending monitoring data to new Central.
        - **scope_id** (string): Scope identifier for the device. This needed for any configuration related actions with the device.
        - **role** (string): Device role in the network
        - **deployment** (string): Deployment mode (e.g., "Standalone", "Stack")
        - **tier** (string, optional): Device License tier classification (e.g., "ADVANCED_AP"). This provides details on which type of Central subscription is used to subscribe the device.
        - **firmware_version** (string): Current firmware version installed on the device
        - **site_id** (string): ID of the site where device is located
        - **site_name** (string): Name of the site where device is located
        - **device_group_name** (string, optional): Name of the device group
        - **ipv4** (string, optional): IPv4 address of the device

    **Example Request:**
    ```
    GET /devices/filter?device_type=ACCESS_POINT&is_provisioned=true&sort=deviceName asc
    ```

    **Example Response:**
      ```json
      [
        {
            "serial_number": "USTWM5206L",
            "mac_address": "ec:1b:5f:c9:92:f3",
            "device_type": "ACCESS_POINT",
            "model": "AP-735-RWF1",
            "part_number": "S1G47A",
            "name": "IMF-BLR-CP-AP02",
            "function": "-",
            "status": "OFFLINE",
            "is_provisioned": true,
            "role": "-",
            "deployment": "Standalone",
            "tier": "ADVANCED_AP",
            "firmware_version": "10.7.2.1_93186",
            "site_id": "48424357225234432",
            "site_name": "IMF-Bengaluru-Campus",
            "device_group_name": null,
            "scope_id": "48407759959924736",
            "ipv4": "172.16.10.55",
            "stack_id": null,
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

    if site_id:
        add_filter("siteId", site_id)
    if device_type:
        add_filter("deviceType", device_type)
    if device_name:
        add_filter("deviceName", device_name)
    if serial_number:
        add_filter("serialNumber", serial_number)
    if model:
        add_filter("model", model)
    if device_function:
        add_filter("deviceFunction", device_function)
    if is_provisioned is not None:
        filter_parts.append(f"isProvisioned eq '{'Yes' if is_provisioned else 'No'}'")

    # Build query parameters
    query_params = {}

    if filter_parts:
        query_params["filter"] = " and ".join(filter_parts)
    if site_assigned:
        query_params["site-assigned"] = site_assigned
    if search:
        query_params["search"] = search
    if sort:
        query_params["sort"] = sort

    # Fetch filtered devices from API
    devices = paginated_fetch(
        get_conn(),
        "network-monitoring/v1alpha1/device-inventory",
        1000,
        additional_params=query_params,
        use_cursor=True,
    )

    cleaned_devices = clean_device_duplicates(devices)

    # Convert to Device instances for proper validation
    return cleaned_devices
