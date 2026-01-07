"""
Repository for model mapping data access.
Handles ERP to CDB model name mapping queries.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.mapping import ModelMapping
from app.core.logging import logger
from app.core.exceptions import DatabaseException


class MappingRepository:
    """Repository for querying model mappings."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_mapped_model(
        self,
        manufacturer: str,
        erp_model: str
    ) -> Optional[str]:
        """
        Get the CDB standardized model name for an ERP model.

        Args:
            manufacturer: Vehicle manufacturer
            erp_model: ERP model name

        Returns:
            CDB standardized model name, or None if not found

        Raises:
            DatabaseException: If database query fails
        """
        try:
            logger.debug(
                f"Looking up model mapping: manufacturer={manufacturer}, erp_model={erp_model}"
            )

            mapping = self.db.query(ModelMapping).filter(
                ModelMapping.manufacturer == manufacturer,
                ModelMapping.erp_name == erp_model
            ).first()

            if mapping:
                logger.info(f"Found mapping: {erp_model} -> {mapping.mapped_name}")
                return mapping.mapped_name
            else:
                logger.warning(f"No mapping found for {manufacturer} {erp_model}")
                return None

        except Exception as e:
            logger.error(f"Database error querying model mapping: {e}")
            raise DatabaseException(f"Failed to query model mapping: {str(e)}")

    def check_model_exists(
        self,
        manufacturer: str,
        erp_model: str
    ) -> bool:
        """
        Check if a model mapping exists.

        Args:
            manufacturer: Vehicle manufacturer
            erp_model: ERP model name

        Returns:
            True if mapping exists, False otherwise

        Raises:
            DatabaseException: If database query fails
        """
        try:
            exists = self.db.query(ModelMapping).filter(
                ModelMapping.manufacturer == manufacturer,
                ModelMapping.erp_name == erp_model
            ).first() is not None

            logger.debug(f"Model mapping exists: {exists} for {manufacturer} {erp_model}")
            return exists

        except Exception as e:
            logger.error(f"Database error checking model existence: {e}")
            raise DatabaseException(f"Failed to check model existence: {str(e)}")
