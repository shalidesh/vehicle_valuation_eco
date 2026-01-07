"""
SQLAlchemy model for ERP model mapping.
Maps ERP model names to CDB standardized names.
"""
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class ModelMapping(Base):
    """
    Model for ERP to CDB model name mapping.
    Maps from erp_model_mapping table (referenced as model_mapping in queries).
    """
    __tablename__ = "erp_model_mapping"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String(100), nullable=False, index=True)  # make in queries
    erp_name = Column(String(100), nullable=False, index=True)  # model in queries
    mapped_name = Column(String(100), nullable=False)  # map_model_name in queries
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Ensure unique manufacturer + ERP name combinations
    __table_args__ = (
        UniqueConstraint('manufacturer', 'erp_name', name='uix_erp_mapping'),
    )

    def __repr__(self):
        return f"<ModelMapping(manufacturer={self.manufacturer}, erp={self.erp_name}, mapped={self.mapped_name})>"
