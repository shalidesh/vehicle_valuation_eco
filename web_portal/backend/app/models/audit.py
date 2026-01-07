from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), index=True)
    operation = Column(String(20))
    user_id = Column(Integer, ForeignKey("users.id"))
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
