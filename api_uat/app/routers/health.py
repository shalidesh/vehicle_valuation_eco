"""
Health check endpoints for monitoring and readiness probes.
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.core.logging import logger

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns OK if the service is running.

    Returns:
        JSON response with health status
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe endpoint.
    Checks if the service can handle requests (database connection, etc.).

    Args:
        db: Database session

    Returns:
        JSON response with readiness status
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))

        logger.debug("Readiness check passed")

        return {
            "status": "ready",
            "service": settings.app_name,
            "database": "connected"
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not ready",
                "service": settings.app_name,
                "database": "disconnected",
                "error": str(e)
            }
        )
