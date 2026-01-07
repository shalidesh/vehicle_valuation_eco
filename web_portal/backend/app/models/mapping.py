from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base


class ERPModelMapping(Base):
    __tablename__ = "erp_model_mapping"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String(100), nullable=False, index=True)
    erp_name = Column(String(100), nullable=False, index=True)
    mapped_name = Column(String(100), nullable=False)
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint('manufacturer', 'erp_name', name='uix_erp_mapping'),
    )
