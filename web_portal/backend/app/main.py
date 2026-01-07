from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, get_settings
from .routers import auth_router, vehicles_router, mapping_router, analytics_router, bulk_upload_router

# NOTE: Table creation is now handled by Alembic migrations
# Database schema is managed via the db_migrations service in docker-compose.yml
# This ensures migrations run before the application starts

app = FastAPI(
    title="CDB Vehicle Portal API",
    description="API for managing vehicle data with role-based access control",
    version="1.0.0",
)

# Configure CORS
settings = get_settings()
origins = settings.cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(vehicles_router)
app.include_router(mapping_router)
app.include_router(analytics_router)
app.include_router(bulk_upload_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CDB Vehicle Portal API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
