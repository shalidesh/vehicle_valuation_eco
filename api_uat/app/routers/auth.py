"""
Authentication router.
Provides login endpoint with HTTP Basic Auth.
Maintains backward compatibility with original API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.schemas.auth import TokenResponse
from app.core.security import verify_basic_auth, create_access_token
from app.core.logging import logger

router = APIRouter(tags=["authentication"])
security = HTTPBasic()


@router.get("/login", response_model=TokenResponse)
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Login endpoint using HTTP Basic Authentication.
    Returns JWT token on successful authentication.

    Backward compatible with original GET /login endpoint.

    Args:
        credentials: HTTP Basic Auth credentials

    Returns:
        TokenResponse with JWT access token

    Raises:
        HTTPException: If credentials are invalid (401)
    """
    username = credentials.username
    password = credentials.password

    # Log login attempt (without password)
    logger.info(f"Login attempt for user: {username}")

    # Verify credentials
    if not verify_basic_auth(username, password):
        logger.warning(f"Invalid credentials for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Create JWT token (Flask format: {'user': username})
    access_token = create_access_token(data={"user": username})

    logger.info(f"Successful login for user: {username}")

    return TokenResponse(token=access_token)
