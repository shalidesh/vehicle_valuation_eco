"""
Repository for vehicle data access.
Encapsulates database queries for scraped vehicles.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.vehicle import ScrapedVehicle
from app.core.logging import logger
from app.core.exceptions import DatabaseException


class VehicleRepository:
    """Repository for querying vehicle data."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_vehicles_by_filters(
        self,
        manufacturer: str,
        model: str,
        yom: int
    ) -> List[ScrapedVehicle]:
        """
        Get vehicles matching the specified filters.
        Used for price estimation.

        Args:
            manufacturer: Vehicle manufacturer (e.g., 'TOYOTA')
            model: Vehicle model name (CDB standardized name)
            yom: Year of manufacture

        Returns:
            List of matching ScrapedVehicle records

        Raises:
            DatabaseException: If database query fails
        """
        try:
            logger.debug(
                f"Querying vehicles: manufacturer={manufacturer}, model={model}, yom={yom}"
            )

            logger.info(
                f"Querying vehicles: manufacturer={manufacturer}, model={model}, yom={yom}"
            )

            vehicles = self.db.query(ScrapedVehicle).filter(
                func.trim(ScrapedVehicle.manufacturer) == func.trim(manufacturer), 
                func.trim(ScrapedVehicle.model) == func.trim(model), 
                ScrapedVehicle.yom == yom
            ).all()

            logger.info(f"Found {len(vehicles)} matching vehicles")
            return vehicles

        except Exception as e:
            logger.error(f"Database error querying vehicles: {e}")
            raise DatabaseException(f"Failed to query vehicles: {str(e)}")

    def get_vehicle_count(
        self,
        manufacturer: str,
        model: str,
        yom: int
    ) -> int:
        """
        Get count of vehicles matching the filters.

        Args:
            manufacturer: Vehicle manufacturer
            model: Vehicle model name
            yom: Year of manufacture

        Returns:
            Count of matching vehicles
        """
        try:
            count = self.db.query(ScrapedVehicle).filter(
                func.trim(ScrapedVehicle.manufacturer) == func.trim(manufacturer), 
                func.trim(ScrapedVehicle.model) == func.trim(model), 
                ScrapedVehicle.yom == yom
            ).count()

            return count

        except Exception as e:
            logger.error(f"Database error counting vehicles: {e}")
            raise DatabaseException(f"Failed to count vehicles: {str(e)}")
