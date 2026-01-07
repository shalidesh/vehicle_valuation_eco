from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


# Fast Moving Vehicle Schemas
class FastMovingVehicleBase(BaseModel):
    type: str = Field(..., max_length=20)  # Registered or Unregistered
    manufacturer: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    yom: int = Field(..., ge=1900, le=2100)
    price: Optional[Decimal] = None
    date: datetime  # Date when the price was recorded


class FastMovingVehicleCreate(FastMovingVehicleBase):
    pass


class FastMovingVehicleUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=20)  # Registered or Unregistered
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    yom: Optional[int] = Field(None, ge=1900, le=2100)
    price: Optional[Decimal] = None
    date: Optional[datetime] = None  # Date when the price was recorded


class FastMovingVehicleResponse(FastMovingVehicleBase):
    id: int
    updated_date: datetime
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


# Scraped Vehicle Schemas
class ScrapedVehicleBase(BaseModel):
    type: str = Field(..., max_length=100)  # Registered or Unregistered
    manufacturer: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    yom: int = Field(..., ge=1900, le=2100)
    transmission: Optional[str] = Field(None, max_length=50)
    fuel_type: Optional[str] = Field(None, max_length=50)
    mileage: Optional[int] = Field(None, ge=0)
    price: Optional[Decimal] = None


class ScrapedVehicleCreate(ScrapedVehicleBase):
    pass


class ScrapedVehicleUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=100)  # Registered or Unregistered
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    yom: Optional[int] = Field(None, ge=1900, le=2100)
    transmission: Optional[str] = Field(None, max_length=50)
    fuel_type: Optional[str] = Field(None, max_length=50)
    mileage: Optional[int] = Field(None, ge=0)
    price: Optional[Decimal] = None


class ScrapedVehicleResponse(ScrapedVehicleBase):
    id: int
    updated_date: datetime

    class Config:
        from_attributes = True
