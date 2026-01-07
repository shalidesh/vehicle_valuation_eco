from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base


class FastMovingVehicle(Base):
    __tablename__ = "fast_moving_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, index=True)  # Registered or Unregistered
    manufacturer = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    yom = Column(Integer, nullable=False)
    price = Column(DECIMAL(15, 2))
    date = Column(DateTime(timezone=True), nullable=False, index=True)  # User-specified date when price was recorded
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))

    __table_args__ = (
        Index('idx_fast_moving_price_movement', 'type', 'manufacturer', 'model', 'yom', 'date'),
        UniqueConstraint('type', 'manufacturer', 'model', 'yom', 'date', name='uix_fast_moving_vehicle_date'),
    )


class ScrapedVehicle(Base):
    __tablename__ = "scraped_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String(100), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    yom = Column(Integer, nullable=False, index=True)
    transmission = Column(String(50))
    fuel_type = Column(String(50))
    mileage = Column(Integer)
    price = Column(DECIMAL(15, 2))
    updated_date = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_scraped_price_movement', 'manufacturer', 'model','type', 'yom', 'updated_date'),
    )
