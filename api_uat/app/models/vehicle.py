"""
SQLAlchemy models for vehicle-related tables.
Maps to scraped_vehicles table in the database.
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Index
from sqlalchemy.sql import func
from app.database import Base


class ScrapedVehicle(Base):
    """
    Model for scraped vehicles data from web scraping.
    Used for price estimation and market analysis.
    """
    __tablename__ = "scraped_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String(100), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)  # Registered/Unregistered
    model = Column(String(100), nullable=False, index=True)
    yom = Column(Integer, nullable=False, index=True)  # Year of manufacture
    transmission = Column(String(50))
    fuel_type = Column(String(50))
    mileage = Column(Integer)
    price = Column(DECIMAL(15, 2))
    updated_date = Column(DateTime(timezone=True), server_default=func.now())

    # Composite index for efficient price queries
    __table_args__ = (
        Index('idx_scraped_price_lookup', 'manufacturer', 'model', 'type', 'yom'),
    )

    def __repr__(self):
        return f"<ScrapedVehicle(id={self.id}, make={self.manufacturer}, model={self.model}, yom={self.yom}, price={self.price})>"
