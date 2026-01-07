"""
Price prediction service containing the core business logic.
Implements the same algorithm as the original price_calculation.py.
"""
import pandas as pd
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
        """
        Initialize prediction service with repositories.

        Args:
            vehicle_repo: Vehicle data repository
            mapping_repo: Model mapping repository
        """
        self.vehicle_repo = vehicle_repo
        self.mapping_repo = mapping_repo

    def estimate_price(
        self,
        manufacturer: str,
        erp_model: str,
        year: str
    ) -> Tuple[float, str]:
        """
        Estimate vehicle price using market data.
        Implements the same algorithm as original utils/price_calculation.py.

        Algorithm:
        1. Map ERP model to CDB standardized model
        2. Fetch matching vehicles from database
        3. If >= 5 records: Use IQR outlier removal + mean
        4. If < 5 records: Use direct mean of matching year
        5. Apply 2% reduction (except for BYD)
        6. Round to nearest 50,000

        Args:
            manufacturer: Vehicle manufacturer (e.g., 'TOYOTA')
            erp_model: ERP model name
            year: Year of manufacture as string

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

            # Step 2: Fetch matching vehicles
            year_int = int(year)
            vehicles = self.vehicle_repo.get_vehicles_by_filters(
                manufacturer=manufacturer,
                model=cdb_model,
                yom=year_int
            )

            if not vehicles:
                logger.info(f"No matching records found for {cdb_model}")
                return 0, 'no matching records found'

            # Step 3: Convert to pandas DataFrame for calculations
            data = [{
                'price': float(v.price) if v.price else 0,
                'yom': v.yom
            } for v in vehicles]
            selected_data = pd.DataFrame(data)

            # Step 4: Calculate price based on number of records
            if len(selected_data) >= 5:
                # Use IQR method for outlier removal
                Q1 = selected_data["price"].astype(float).quantile(0.25)
                Q3 = selected_data["price"].astype(float).quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                # Filter outliers
                filtered_df = selected_data[
                    (selected_data["price"].astype(float) >= lower_bound) &
                    (selected_data["price"].astype(float) <= upper_bound)
                ]

                estimated_price = filtered_df["price"].astype(float).mean()
                estimated_price = round_nearest_50000(estimated_price)

                logger.info(f"Estimated price (IQR method): {estimated_price}")
                return estimated_price, 'success'

            # Step 5: Less than 5 records - use direct mean
            estimated_price = selected_data[selected_data['yom'] == year_int]['price'].astype(float).mean()

            # Step 6: Apply manufacturer-specific logic
            if manufacturer == 'BYD':
                estimated_price = round(float(estimated_price), 0)
            else:
                estimated_price = round(float(estimated_price), 0) * 0.98
                estimated_price = round_nearest_50000(estimated_price)

            logger.info(f"Estimated price: {estimated_price}")
            return estimated_price, 'success'

        except Exception as e:
            logger.error(f"Error during price estimation: {e}", exc_info=True)
            raise PredictionException(f"Price estimation failed: {str(e)}")
