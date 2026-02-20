"""
Repository for model mapping data access.
Uses fuzzy matching against summery_statistics_table to map ERP model names to DB model names.
"""
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.vehicle import SummaryStatistic
from app.core.logging import logger
from app.core.exceptions import DatabaseException
from app.services.model_matching import ModelIndex, match_vehicle_models


class MappingRepository:
    """Repository for fuzzy matching ERP models against summary statistics models."""

    MATCH_THRESHOLD = 60.0

    def __init__(self, db: Session):
        self.db = db
        self._match_cache = {}

    def _get_distinct_models(self) -> List[Tuple[str, str]]:
        """Get distinct (make, model) pairs from summery_statistics_table."""
        try:
            results = self.db.query(
                func.trim(SummaryStatistic.make),
                func.trim(SummaryStatistic.model)
            ).distinct().all()

            return [(row[0], row[1]) for row in results]

        except Exception as e:
            logger.error(f"Database error fetching distinct models: {e}")
            raise DatabaseException(f"Failed to fetch distinct models: {str(e)}")

    def _fuzzy_match(
        self, manufacturer: str, erp_model: str
    ) -> Tuple[Optional[str], float]:
        """
        Fuzzy match an ERP model name against summery_statistics_table models.
        Results are cached per (manufacturer, erp_model) for the lifetime
        of this repository instance to avoid duplicate matching.

        Returns:
            (matched_model_name, score) or (None, 0.0)
        """
        cache_key = (manufacturer.upper().strip(), erp_model.upper().strip())
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        db_entries = self._get_distinct_models()

        if not db_entries:
            logger.warning("No models found in summery_statistics_table")
            self._match_cache[cache_key] = (None, 0.0)
            return None, 0.0

        index = ModelIndex(db_entries)
        combined_text = f"{manufacturer} {erp_model}" if manufacturer else erp_model

        match, score, is_brand_mismatch = match_vehicle_models(
            erp_brand=manufacturer,
            erp_model_text=combined_text,
            db_entries=db_entries,
            threshold=self.MATCH_THRESHOLD,
            index=index
        )

        if match and not is_brand_mismatch and score >= self.MATCH_THRESHOLD:
            db_brand, db_model = match
            logger.info(
                f"Fuzzy matched: ERP '{manufacturer} {erp_model}' -> "
                f"DB '{db_brand} {db_model}', Score: {score}"
            )
            self._match_cache[cache_key] = (db_model, score)
            return db_model, score

        if match and is_brand_mismatch:
            logger.warning(
                f"Brand mismatch for {manufacturer} {erp_model}, ignoring match"
            )

        logger.warning(f"No fuzzy match (score >= {self.MATCH_THRESHOLD}) found for {manufacturer} {erp_model}")
        self._match_cache[cache_key] = (None, 0.0)
        return None, 0.0

    def get_mapped_model(
        self,
        manufacturer: str,
        erp_model: str
    ) -> Optional[str]:
        """
        Get the mapped model name using fuzzy matching against summery_statistics_table.

        Args:
            manufacturer: Vehicle manufacturer
            erp_model: ERP model name

        Returns:
            Matched model name if score > 60, None otherwise

        Raises:
            DatabaseException: If database query fails
        """
        try:
            logger.debug(
                f"Fuzzy matching: manufacturer={manufacturer}, erp_model={erp_model}"
            )

            matched_model, score = self._fuzzy_match(manufacturer, erp_model)
            print(f"Fuzzy match result: {matched_model} with score {score}")

            if matched_model:
                logger.info(f"Found mapping: {erp_model} -> {matched_model} (score: {score})")
                return matched_model

            logger.warning(f"No mapping found for {manufacturer} {erp_model}")
            return None

        except Exception as e:
            logger.error(f"Error during fuzzy model matching: {e}")
            raise DatabaseException(f"Failed to fuzzy match model: {str(e)}")

    def check_model_exists(
        self,
        manufacturer: str,
        erp_model: str
    ) -> bool:
        """
        Check if a model can be fuzzy matched with score > 60.

        Args:
            manufacturer: Vehicle manufacturer
            erp_model: ERP model name

        Returns:
            True if match found with score > 60, False otherwise

        Raises:
            DatabaseException: If database query fails
        """
        try:
            matched_model, score = self._fuzzy_match(manufacturer, erp_model)
            exists = matched_model is not None
            logger.debug(f"Model fuzzy match exists: {exists} for {manufacturer} {erp_model}")
            return exists

        except Exception as e:
            logger.error(f"Error checking fuzzy match existence: {e}")
            raise DatabaseException(f"Failed to check fuzzy match: {str(e)}")
