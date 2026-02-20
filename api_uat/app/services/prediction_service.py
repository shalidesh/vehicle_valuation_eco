"""
Price prediction service containing the core business logic.
Uses pre-computed average prices from summery_statistics_table.
"""
from typing import Tuple
from app.repositories.vehicle_repository import VehicleRepository
from app.repositories.mapping_repository import MappingRepository
from app.core.logging import logger
from app.core.exceptions import PredictionException


def round_nearest_50000(number: float) -> float:
    """Round number to nearest 50,000."""
    return round(number / 50000) * 50000


class PredictionService:
    """Service for vehicle price prediction."""

    def __init__(
        self,
        vehicle_repo: VehicleRepository,
        mapping_repo: MappingRepository
    ):
        self.vehicle_repo = vehicle_repo
        self.mapping_repo = mapping_repo

    def estimate_price(
        self,
        manufacturer: str,
        erp_model: str,
        year: str,
        transmission: str,
        fuel_type: str
    ) -> Tuple[float, str]:
        """
        Estimate vehicle price using pre-computed summary statistics.

        Algorithm:
        1. Map ERP model to CDB standardized model
        2. Try exact match (make, model, yom, transmission, fuel_type)
        3. If no exact match, fallback to (make, model, yom) average
        4. Apply 2% reduction (except for BYD)
        5. Round to nearest 50,000

        Args:
            manufacturer: Vehicle manufacturer (e.g., 'TOYOTA')
            erp_model: ERP model name
            year: Year of manufacture as string
            transmission: Transmission type (e.g., 'AUTOMATIC')
            fuel_type: Fuel type (e.g., 'HYBRID')

        Returns:
            Tuple of (estimated_price, flag_status)
        """
        try:
            # Step 1: Get CDB standardized model name
            cdb_model = self.mapping_repo.get_mapped_model(manufacturer, erp_model)
            logger.info(f"CDB model is {cdb_model}")

            if not cdb_model:
                logger.info(f"Not a valid model: {erp_model}")
                return 0, 'not valid model'

            year_int = int(year)

            # Step 2: Try exact match with all filters
            price = self.vehicle_repo.get_price_by_filters(
                make=manufacturer,
                model=cdb_model,
                yom=year_int,
                transmission=transmission,
                fuel_type=fuel_type
            )

            # Step 3: Fallback to make/model/yom only
            if price is None:
                logger.info("Exact match not found, trying fallback (make, model, yom)")
                price = self.vehicle_repo.get_price_by_make_model_yom(
                    make=manufacturer,
                    model=cdb_model,
                    yom=year_int
                )

            if price is None:
                logger.info(f"No matching records found for {cdb_model}")
                return 0, 'no matching records found'

            # Step 4: Apply manufacturer-specific logic
            if manufacturer == 'BYD':
                estimated_price = round(price, 0)
            else:
                estimated_price = round(price, 0) * 0.98
                estimated_price = round_nearest_50000(estimated_price)

            logger.info(f"Estimated price: {estimated_price}")
            return estimated_price, 'success'

        except Exception as e:
            logger.error(f"Error during price estimation: {e}", exc_info=True)
            raise PredictionException(f"Price estimation failed: {str(e)}")
