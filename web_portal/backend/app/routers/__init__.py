from .auth import router as auth_router
from .vehicles import router as vehicles_router
from .mapping import router as mapping_router
from .analytics import router as analytics_router
from .bulk_upload import router as bulk_upload_router

__all__ = ["auth_router", "vehicles_router", "mapping_router", "analytics_router", "bulk_upload_router"]
