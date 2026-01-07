"""
Main FastAPI application.
Entry point for the CDB Vehicle Valuation API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.core.logging import logger, start_log_cleanup_scheduler
from app.core.exceptions import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import auth_router, prediction_router, health_router


# Scheduler instance for log cleanup
log_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # Start log cleanup scheduler
    global log_scheduler
    log_scheduler = start_log_cleanup_scheduler()
    logger.info("Log cleanup scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down application")
    if log_scheduler:
        log_scheduler.shutdown()
        logger.info("Log cleanup scheduler stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="API for vehicle price prediction with industry-standard architecture",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Include routers (maintaining backward compatibility - no /api/v1 prefix)
app.include_router(auth_router)
app.include_router(prediction_router)
app.include_router(health_router)

@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
