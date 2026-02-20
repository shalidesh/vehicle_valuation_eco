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


# Summary Statistic Schemas
class SummaryStatisticBase(BaseModel):
    make: str = Field(..., max_length=255)
    model: str = Field(..., max_length=255)
    yom: str = Field(..., max_length=255)
    transmission: str = Field(..., max_length=255)
    fuel_type: str = Field(..., max_length=255)
    average_price: Optional[float] = None
    updated_date: Optional[str] = None


class SummaryStatisticCreate(SummaryStatisticBase):
    pass


class SummaryStatisticUpdate(BaseModel):
    average_price: Optional[float] = None
    updated_date: Optional[str] = None


class SummaryStatisticResponse(SummaryStatisticBase):
    class Config:
        from_attributes = True
