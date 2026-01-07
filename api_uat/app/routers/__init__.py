"""
API routers for handling HTTP requests.
"""
from app.routers.auth import router as auth_router
from app.routers.prediction import router as prediction_router
from app.routers.health import router as health_router

__all__ = ['auth_router', 'prediction_router', 'health_router']
