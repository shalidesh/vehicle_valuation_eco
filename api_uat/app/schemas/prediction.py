"""
Pydantic schemas for prediction request and response.
Maintains backward compatibility with original API format.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PredictionRequest(BaseModel):
    """
    Request schema for vehicle price prediction.
    Matches original API request format for backward compatibility.
    """
    manufacture: str = Field(..., min_length=1, max_length=100, description="Vehicle manufacturer")
    model: str = Field(..., min_length=1, max_length=100, description="Vehicle model name")
    fuel: str = Field(..., min_length=1, max_length=50, description="Fuel type")
    transmission: str = Field(..., min_length=1, max_length=50, description="Transmission type")
    engine_capacity: str = Field(..., description="Engine capacity (e.g., '1500CC', '2000')")
    yom: str = Field(..., pattern=r'^\d{4}$', description="Year of manufacture (4 digits)")

    class Config:
        json_schema_extra = {
            "example": {
                "manufacture": "TOYOTA",
                "model": "PRIUS",
                "fuel": "HYBRID",
                "transmission": "AUTOMATIC",
                "engine_capacity": "1800CC",
                "yom": "2018"
            }
        }


class PredictionResponse(BaseModel):
    """
    Response schema for vehicle price prediction.
    Matches original API response format for backward compatibility.
    """
    flag: str = Field(..., description="Status flag (success, error, etc.)")
    timestamps: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    Predicted_Price: str = Field(..., description="Predicted price as string")
    host_id: str = Field(..., description="Server hostname")

    class Config:
        json_schema_extra = {
            "example": {
                "flag": "success",
                "timestamps": "2025-03-26T12:00:00",
                "Predicted_Price": "5500000",
                "host_id": "api-server-01"
            }
        }
