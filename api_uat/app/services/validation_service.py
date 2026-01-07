"""
Input validation service.
Ported from original utils/input_data_validation.py.
"""
import re
from typing import Optional
from app.core.logging import logger


# Validation constants
TRANSMISSION_LIST = ["AUTOMATIC", "MANUAL", "TIPTRONIC", "TIP TONIC"]
FUEL_LIST = ["PETROL", "DIESEL", "HYBRID", "ELECTRIC", "PETROL+ELECTRIC", "PETROL + ELECTRIC"]
VALID_MANUFACTURERS = [
    'HONDA', 'NISSAN', 'SUZUKI', 'TOYOTA', 'MICRO', 'MITSUBISHI',
    'MAHINDRA', 'MAZDA', 'DAIHATSU', 'HYUNDAI', 'KIA', 'PERODUA', 'BYD'
]


class ValidationService:
    """Service for input validation."""

    @staticmethod
    def validate_transmission(transmission: str) -> bool:
        """
        Check if transmission type is valid.

        Args:
            transmission: Transmission type (e.g., 'AUTOMATIC')

        Returns:
            True if valid, False otherwise
        """
        return transmission in TRANSMISSION_LIST

    @staticmethod
    def validate_fuel_type(fuel: str) -> bool:
        """
        Check if fuel type is valid.

        Args:
            fuel: Fuel type (e.g., 'PETROL')

        Returns:
            True if valid, False otherwise
        """
        return fuel in FUEL_LIST

    @staticmethod
    def validate_yom(yom: str) -> bool:
        """
        Check if year of manufacture is valid (>= 2000).

        Args:
            yom: Year of manufacture as string

        Returns:
            True if valid, False otherwise
        """
        try:
            return int(yom) >= 2000
        except ValueError:
            return False

    @staticmethod
    def validate_manufacturer(manufacturer: str) -> bool:
        """
        Check if manufacturer is in the valid list.

        Args:
            manufacturer: Manufacturer name

        Returns:
            True if valid, False otherwise
        """
        return manufacturer in VALID_MANUFACTURERS

    @staticmethod
    def change_capacity(engine_capacity: str) -> Optional[int]:
        """
        Extract numeric engine capacity from string.
        Examples: '1500CC' -> 1500, '2000' -> 2000

        Args:
            engine_capacity: Engine capacity string

        Returns:
            Numeric capacity or None if invalid
        """
        try:
            match = re.search(r'\d+', engine_capacity)
            if match:
                return int(match.group())
            return None
        except Exception as e:
            logger.error(f"Error extracting engine capacity: {e}")
            return None

    @staticmethod
    def change_transmission(transmission: str) -> str:
        """
        Normalize transmission type.
        Maps 'TIP TONIC' to 'TIPTRONIC'.

        Args:
            transmission: Transmission type

        Returns:
            Normalized transmission type
        """
        if transmission == 'TIP TONIC':
            return 'TIPTRONIC'
        return transmission

    @staticmethod
    def change_fuel_type(fuel: str) -> str:
        """
        Normalize fuel type.
        Maps 'PETROL+ELECTRIC' and 'PETROL + ELECTRIC' to 'HYBRID'.

        Args:
            fuel: Fuel type

        Returns:
            Normalized fuel type
        """
        if fuel in ['PETROL+ELECTRIC', 'PETROL + ELECTRIC']:
            return 'HYBRID'
        return fuel

    @staticmethod
    def validate_all_inputs(
        manufacturer: str,
        fuel: str,
        transmission: str,
        yom: str,
        engine_capacity: str
    ) -> bool:
        """
        Validate all inputs for price prediction.
        Ported from original checkInputs() function.

        Args:
            manufacturer: Vehicle manufacturer
            fuel: Fuel type
            transmission: Transmission type
            yom: Year of manufacture
            engine_capacity: Engine capacity

        Returns:
            True if all inputs are valid, False otherwise
        """
        # Extract numeric capacity
        capacity_numeric = ValidationService.change_capacity(engine_capacity)

        # Check all fields are present
        if not all([manufacturer, fuel, transmission, yom, capacity_numeric]):
            logger.warning("Missing required fields")
            return False

        # Validate each field
        if not ValidationService.validate_transmission(transmission):
            logger.warning(f"Invalid transmission: {transmission}")
            return False

        if not ValidationService.validate_fuel_type(fuel):
            logger.warning(f"Invalid fuel type: {fuel}")
            return False

        if not ValidationService.validate_yom(yom):
            logger.warning(f"Invalid year of manufacture: {yom}")
            return False

        if not ValidationService.validate_manufacturer(manufacturer):
            logger.warning(f"Invalid manufacturer: {manufacturer}")
            return False

        logger.info("All input validations passed")
        return True
