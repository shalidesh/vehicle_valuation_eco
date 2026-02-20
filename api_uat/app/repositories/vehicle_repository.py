"""
Repository for vehicle price data access.
Queries the summery_statistics_table for pre-computed average prices.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.vehicle import SummaryStatistic
from app.core.logging import logger
from app.core.exceptions import DatabaseException


class VehicleRepository:
    """Repository for querying vehicle summary statistics."""

    def __init__(self, db: Session):
        self.db = db

    def get_price_by_filters(
        self,
        make: str,
        model: str,
        yom: int,
        transmission: str,
        fuel_type: str
    ) -> Optional[float]:
        """
        Get pre-computed average price with exact match on all filters.

        Args:
            make: Vehicle manufacturer
            model: Vehicle model name (CDB standardized)
            yom: Year of manufacture
            transmission: Transmission type
            fuel_type: Fuel type

        Returns:
            Average price if found, None otherwise
        """
        try:
            yom_str = str(yom)
            logger.info(
                f"Querying summary stats: make={make}, model={model}, "
                f"yom={yom_str}, transmission={transmission}, fuel_type={fuel_type}"
            )

            result = self.db.query(SummaryStatistic.average_price).filter(
                func.upper(func.trim(SummaryStatistic.make)) == func.upper(func.trim(make)),
                func.upper(func.trim(SummaryStatistic.model)) == func.upper(func.trim(model)),
                func.trim(SummaryStatistic.yom) == func.trim(yom_str),
                func.upper(func.trim(SummaryStatistic.transmission)) == func.upper(func.trim(transmission)),
                func.upper(func.trim(SummaryStatistic.fuel_type)) == func.upper(func.trim(fuel_type)),
            ).order_by(desc(SummaryStatistic.updated_date)).first()

            if result and result[0] is not None:
                logger.info(f"Found exact match price: {result[0]}")
                return float(result[0])

            logger.info("No exact match found in summary statistics")
            return None

        except Exception as e:
            logger.error(f"Database error querying summary stats: {e}")
            raise DatabaseException(f"Failed to query summary statistics: {str(e)}")

    def get_price_by_make_model_yom(
        self,
        make: str,
        model: str,
        yom: int
    ) -> Optional[float]:
        """
        Get average price matching by make, model, yom only (fallback).
        Averages across different transmission/fuel_type combinations.

        Args:
            make: Vehicle manufacturer
            model: Vehicle model name (CDB standardized)
            yom: Year of manufacture

        Returns:
            Average price if found, None otherwise
        """
        try:
            yom_str = str(yom)
            logger.info(
                f"Querying summary stats (fallback): make={make}, model={model}, yom={yom_str}"
            )

            results = self.db.query(SummaryStatistic.average_price).filter(
                func.upper(func.trim(SummaryStatistic.make)) == func.upper(func.trim(make)),
                func.upper(func.trim(SummaryStatistic.model)) == func.upper(func.trim(model)),
                func.trim(SummaryStatistic.yom) == func.trim(yom_str),
            ).all()

            if results:
                prices = [float(r[0]) for r in results if r[0] is not None]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    logger.info(f"Found {len(prices)} records, average price: {avg_price}")
                    return avg_price

            logger.info("No records found in summary statistics")
            return None

        except Exception as e:
            logger.error(f"Database error querying summary stats: {e}")
            raise DatabaseException(f"Failed to query summary statistics: {str(e)}")
