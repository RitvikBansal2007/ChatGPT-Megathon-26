"""FastAPI application factory, middleware, and global exception handlers."""

import sqlite3
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.dependencies import is_auth_configured
from backend.api.routers import transactions
from backend.api.schemas import HealthResponse
from backend.config import Settings, get_settings
from backend.db import get_connection


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Application factory for the GreenProof backend."""
    app_settings = settings or get_settings()

    # Fail closed in production if mandatory authentication is unavailable
    if app_settings.ENVIRONMENT == "production" and not is_auth_configured():
        raise RuntimeError(
            "Production startup failed: authentication is mandatory but no auth provider is configured."
        )

    app = FastAPI(
        title="GreenProof Core API",
        description="Core banking and transaction backend for GreenProof",
        version="0.1.0",
        docs_url="/docs" if app_settings.ENVIRONMENT != "production" else None,
        redoc_url=None,
    )

    # CORS configuration from explicit allowlist
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Safe global exception handlers
    @app.exception_handler(sqlite3.IntegrityError)
    async def sqlite_integrity_error_handler(request: Request, exc: sqlite3.IntegrityError):
        """Sanitized handler for database constraint violations."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "A database constraint was violated. Duplicate record or invalid reference."},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Sanitized handler for unhandled exceptions to prevent stack trace or path leaks."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )

    # System Health and Readiness
    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health_check():
        """Liveness check returning basic service status."""
        return {"status": "ok", "environment": app_settings.ENVIRONMENT}

    @app.get("/ready", response_model=HealthResponse, tags=["system"])
    def readiness_check():
        """Readiness check verifying database connectivity safely."""
        try:
            conn = get_connection(app_settings.GREENPROOF_DB_PATH)
            conn.execute("SELECT 1;")
            conn.close()
            return {"status": "ok", "environment": app_settings.ENVIRONMENT}
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unavailable", "environment": app_settings.ENVIRONMENT},
            )

    # Register API routers
    app.include_router(transactions.router)

    return app


# Default app instance for ASGI servers (e.g. uvicorn backend.api.app:app)
app = create_app()
