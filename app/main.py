from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.core.config import settings
from app.core.exceptions import NextShiftException


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="NextShift: Campus Part-time Job Marketplace Backend API",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Domain Exception Handling (Polymorphic error handling)
    @app.exception_handler(NextShiftException)
    async def nextshift_exception_handler(request: Request, exc: NextShiftException):
        content = {"detail": exc.detail}
        if exc.data:
            content["data"] = exc.data
        return JSONResponse(status_code=exc.status_code, content=content)

    # Mount Routers
    # Health check is public at root /health
    app.include_router(health_router)

    # API v1 routes
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(jobs_router, prefix=settings.API_V1_STR)
    app.include_router(bookings_router, prefix=settings.API_V1_STR)
    app.include_router(admin_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
