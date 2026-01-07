from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ERPModelMappingBase(BaseModel):
    manufacturer: str = Field(..., max_length=100)
    erp_name: str = Field(..., max_length=100)
    mapped_name: str = Field(..., max_length=100)


class ERPModelMappingCreate(ERPModelMappingBase):
    pass


class ERPModelMappingUpdate(BaseModel):
    manufacturer: Optional[str] = Field(None, max_length=100)
    erp_name: Optional[str] = Field(None, max_length=100)
    mapped_name: Optional[str] = Field(None, max_length=100)


class ERPModelMappingResponse(ERPModelMappingBase):
    id: int
    updated_date: datetime
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True
