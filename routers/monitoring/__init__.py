# Routers package
from .sites import router as sites_router
from .devices import router as devices_router
from .clients import router as clients_router
from .alerts import router as alerts_router
from .application_visibility import router as application_visibility_router
from .audit_trail import router as audit_trail_router
from .events import router as events_router

__all__ = [
    "sites_router",
    "devices_router",
    "clients_router",
    "alerts_router",
    "application_visibility_router",
    "audit_trail_router",
    "events_router",
]
