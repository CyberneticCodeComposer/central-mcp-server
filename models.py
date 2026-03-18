from typing import Dict, Any
from pydantic import BaseModel, Field

from enum import Enum


class SourceType(str, Enum):
    ACCESS_POINT = "Access Point"
    SWITCH = "Switch"
    GATEWAY = "Gateway"
    WIRELESS_CLIENT = "Wireless Client"
    WIRED_CLIENT = "Wired Client"
    BRIDGE = "Bridge"


class SiteMetrics(BaseModel):
    """Standardized site metrics structure"""

    health: Dict[str, Any] = Field(default_factory=dict)
    devices: Dict[str, Any] = Field(default_factory=dict)
    clients: Dict[str, Any] = Field(default_factory=dict)
    alerts: Dict[str, Any] | int = Field(default_factory=dict)


class SiteData(BaseModel):
    """Standardized site data structure"""

    site_id: str
    name: str
    address: dict
    location: dict
    metrics: SiteMetrics


class Device(BaseModel):
    """Device inventory data structure (duplicates removed)"""

    # Primary identifiers
    serial_number: str
    mac_address: str

    # Device information
    device_type: str
    model: str
    part_number: str
    name: str
    function: str | None

    # Status and configuration
    status: str | None
    is_provisioned: bool
    role: str | None
    deployment: str | None
    tier: str | None

    # Version information
    firmware_version: str | None

    # Location and grouping
    site_id: str | None
    site_name: str | None
    device_group_name: str | None
    scope_id: str | None

    # Network information
    ipv4: str | None

    # Additional metadata
    stack_id: str | None


class Client(BaseModel):
    """Client device data structure"""

    # Primary identifiers
    mac: str | None
    name: str | None
    ipv4: str | None
    ipv6: str | None
    hostname: str | None

    # Client classification
    type: str | None
    vendor: str | None
    manufacturer: str | None
    category: str | None
    function: str | None
    model_os: str | None
    capabilities: str | None

    # Status and health
    status: str | None
    status_reason: str | None
    health: str | None

    # Connection information
    connected_device_type: str | None
    connected_device_serial: str | None
    connected_to: str | None
    connected_since: str | None
    last_seen_at: str | None
    port: str | None

    # Network configuration
    network: str | None
    vlan_id: str | None
    tunnel: str | None
    tunnel_id: int | None

    # Wireless-specific fields
    ssid: str | None
    wireless_band: str | None
    wireless_channel: str | None
    wireless_security: str | None
    key_management: str | None
    vap_bssid: str | None
    radio_mac: str | None

    # Authentication
    user_name: str | None
    authentication: str | None

    # Site information
    site_id: str | None
    site_name: str | None

    # Additional metadata
    role: str | None
    tags: str | None


class Alert(BaseModel):
    summary: str
    clearedReason: str | None
    createdAt: str
    priority: str
    updatedAt: str | None
    deviceType: str | None
    updatedBy: str | None
    name: str | None
    status: str | None
    category: str | None
    severity: str | None


class ApplicationVisibility(BaseModel):
    experience: dict | None
    dest_location: list[dict] | None
    risk: str | None
    application_host_type: str | None
    name: str | None
    tx_bytes: int | None
    rx_bytes: int | None
    last_used_time: str | None
    tls_version: str | None
    certificate_expiry_date: str | None
    categories: list[str] | None
    state: str | None


class Event(BaseModel):
    eventId: str
    """The event type identifier"""

    eventIdentifier: str
    """Unique identifier for the event."""

    serialNumber: str
    """Device serial number"""

    timeAt: str
    """Timestamp when the event occurred at the source, in RFC 3339 format with milliseconds."""

    eventName: str
    """Name of the event."""

    category: str
    """Event category."""

    sourceType: SourceType
    """Type of source that generated the event."""

    sourceName: str
    """Name of the device or client that generated the event."""

    description: str
    """Detailed description of the event."""

    clientMacAddress: str | None
    """MAC address of the client involved in the event."""

    deviceMacAddress: str | None
    """MAC address of the device that generated the event."""

    stackId: str | None
    """Stack identifier for stack-capable devices."""

    bssid: str | None
    """Basic Service Set Identifier for wireless events."""

    reason: str | None
    """Reason or cause of the event."""

    severity: str | None
    """Severity level of the event."""
