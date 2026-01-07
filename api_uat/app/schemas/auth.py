"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """
    Response schema for login endpoint.
    Matches original API response format.
    """
    token: str = Field(..., description="JWT access token")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
