from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router

__all__ = [
    "admin_router",
    "auth_router",
    "bookings_router",
    "health_router",
    "jobs_router",
]
