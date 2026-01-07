"""
Middleware for cross-cutting concerns.
"""
from app.middleware.logging_middleware import LoggingMiddleware

__all__ = ['LoggingMiddleware']
