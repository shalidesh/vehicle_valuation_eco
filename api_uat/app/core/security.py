"""
Security utilities for authentication and authorization.
Handles JWT token generation, validation, and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.core.logging import logger
from app.core.exceptions import AuthenticationException

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token without expiration (matching Flask implementation).

    Creates tokens in the format: {'user': username}
    These tokens never expire, maintaining backward compatibility.

    Args:
        data: Data to encode in the token (e.g., {'user': username})
        expires_delta: Optional custom expiration time (not used, for compatibility)

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    # Do NOT add expiration - tokens never expire (Flask compatibility)
    # Just encode the user data: {'user': username}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token (matching Flask implementation).

    Tokens do not expire and contain: {'user': username}
    Maintains backward compatibility with old Flask tokens.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        AuthenticationException: If token is invalid
    """
    # Check if using fixed access token (alternative authentication method)

    logger.info("Verifying token",settings.fixed_access_token )
    logger.info("Verifying token",token )
    if settings.fixed_access_token and token == settings.fixed_access_token:
        logger.info("Authentication using fixed access token")
        return {
            "user": settings.auth_username,
            "fixed": True
        }

    # Verify JWT token (no expiration check - Flask compatibility)
    try:
        # Decode without expiration verification
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False}  # Don't verify expiration (Flask compatibility)
        )

        # Verify token has 'user' field (Flask format)
        if "user" not in payload:
            raise AuthenticationException("Invalid token format")

        return payload

    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise AuthenticationException("Invalid token")
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise AuthenticationException("Token verification error")


def verify_basic_auth(username: str, password: str) -> bool:
    """
    Verify basic authentication credentials.

    Args:
        username: Username
        password: Password

    Returns:
        True if credentials are valid, False otherwise
    """
    # Check against configured credentials
    return (
        username == settings.auth_username and
        password == settings.auth_password
    )


__all__ = [
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'verify_token',
    'verify_basic_auth'
]
