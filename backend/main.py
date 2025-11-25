"""
Module: main
Purpose: FastAPI application entry point
Dependencies: FastAPI, Uvicorn, Starlette

Main FastAPI application with middleware, CORS configuration, and API routes.

This module initializes the FastAPI app, sets up middleware, and defines
the basic route structure.

Running the Application:
    # Development (with auto-reload)
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

    # Production
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

Environment Variables (from .env):
    - DATABASE_URL: PostgreSQL connection string
    - DEBUG: Enable debug mode
    - And more (see backend/config.py)

Example:
    >>> from backend.main import app
    >>> # Use with: uvicorn backend.main:app --reload

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from backend.config import settings
from backend.database import SessionLocal, get_db
from backend.sync import SyncScheduler

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered practice management system for Xero and QuickBooks",
    version=settings.app_version,
    debug=settings.debug,
    openapi_url="/api/v1/openapi.json" if settings.debug else None,
    docs_url="/api/v1/docs" if settings.debug else None,
    redoc_url="/api/v1/redoc" if settings.debug else None,
)

# Global scheduler instance
_scheduler: Optional[SyncScheduler] = None

# Add CORS middleware
# Allows frontend to make requests to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming HTTP requests.

    Logs request method, path, and response status code.
    Helps with debugging and monitoring.

    Args:
        request: Incoming request
        call_next: Next middleware/route handler

    Returns:
        Response from next handler with logging
    """
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"{response.status_code} {request.method} {request.url.path}")
    return response


# Error handling
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.

    Catches any unhandled exceptions and returns a structured error response.

    Args:
        request: The request that caused the error
        exc: The exception

    Returns:
        JSONResponse with error details
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An error occurred",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint - API information.

    Returns:
        Application information and version
    """
    return {
        "message": "Multi-Platform AI Practice Management System",
        "version": settings.app_version,
        "status": "running",
        "environment": settings.environment,
        "docs": "/api/v1/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Health status and database connection status

    Response:
        {
            "status": "healthy",
            "timestamp": "2025-11-23T21:00:00",
            "database": "connected",
            "version": "2.0.0-alpha"
        }
    """
    try:
        # Try to get a database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": settings.app_version,
        "environment": settings.environment,
    }


# ============================================================================
# API v1 ROUTE STRUCTURE
# ============================================================================
# These routes will be populated in future tasks

@app.get("/api/v1/", tags=["API"])
async def api_v1_root() -> Dict[str, Any]:
    """
    API v1 root endpoint.

    Returns:
        Available endpoints and API information
    """
    return {
        "message": "API v1",
        "version": "1.0.0",
        "endpoints": {
            "organizations": "/api/v1/organizations",
            "clients": "/api/v1/clients",
            "transactions": "/api/v1/transactions",
            "accounts": "/api/v1/accounts",
            "sync": "/api/v1/sync",
            "ai": "/api/v1/ai",
        },
        "docs": "/api/v1/docs",
    }


# ============================================================================
# PLACEHOLDER ROUTES (To be implemented in future tasks)
# ============================================================================


@app.get("/api/v1/organizations", tags=["Organizations"])
async def list_organizations(db=Depends(get_db)) -> Dict[str, Any]:
    """
    List all organizations.

    Currently a placeholder. Will be implemented in Task 4+.

    Args:
        db: Database session (dependency injection)

    Returns:
        List of organizations
    """
    return {
        "message": "Organizations endpoint - Coming soon",
        "status": "placeholder",
    }


@app.get("/api/v1/clients", tags=["Clients"])
async def list_clients(db=Depends(get_db)) -> Dict[str, Any]:
    """
    List all clients.

    Currently a placeholder. Will be implemented in Task 4+.

    Args:
        db: Database session (dependency injection)

    Returns:
        List of clients
    """
    return {
        "message": "Clients endpoint - Coming soon",
        "status": "placeholder",
    }


@app.get("/api/v1/transactions", tags=["Transactions"])
async def list_transactions(db=Depends(get_db)) -> Dict[str, Any]:
    """
    List all transactions.

    Currently a placeholder. Will be implemented in Task 4+.

    Args:
        db: Database session (dependency injection)

    Returns:
        List of transactions
    """
    return {
        "message": "Transactions endpoint - Coming soon",
        "status": "placeholder",
    }


# Include sync routes
from backend.api.sync_routes import router as sync_router
from backend.api.job_routes import router as job_router
from backend.api.dashboard_routes import router as dashboard_router
from backend.api import job_routes as job_routes_module

app.include_router(sync_router, prefix="/api/v1")
app.include_router(job_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/api/v1/ai", tags=["AI"])
async def ai_analysis(db=Depends(get_db)) -> Dict[str, Any]:
    """
    AI analysis endpoints.

    Currently a placeholder. Will be implemented in Phase 2.

    Args:
        db: Database session (dependency injection)

    Returns:
        AI analysis information
    """
    return {
        "message": "AI analysis endpoint - Coming soon",
        "status": "placeholder",
    }


# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================


@app.on_event("startup")
async def startup_event() -> None:
    """
    Application startup event.

    Called when the application starts.
    Use for initialization tasks (logging, database checks, etc.)
    """
    global _scheduler

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database: {settings.database_url}")

    # Initialize sync scheduler
    try:
        _scheduler = SyncScheduler(SessionLocal())
        job_routes_module.set_scheduler(_scheduler)
        _scheduler.start()
        logger.info("Sync scheduler initialized and started")
    except Exception as e:
        logger.error(f"Failed to initialize sync scheduler: {e}", exc_info=True)
        # Don't fail startup if scheduler fails, but log the error

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Application shutdown event.

    Called when the application is shutting down.
    Use for cleanup tasks (closing connections, saving state, etc.)
    """
    global _scheduler

    logger.info(f"Shutting down {settings.app_name}")

    # Stop sync scheduler
    if _scheduler:
        try:
            _scheduler.stop()
            logger.info("Sync scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping sync scheduler: {e}", exc_info=True)

    logger.info("Application shut down successfully")


if __name__ == "__main__":
    import uvicorn

    # Run with: python -m backend.main
    # Or: uvicorn backend.main:app --reload
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
