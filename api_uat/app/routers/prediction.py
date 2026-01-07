"""
Prediction router for vehicle price estimation.
Main API endpoint maintaining backward compatibility.
"""
import socket
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import PredictionService
from app.services.validation_service import ValidationService
from app.repositories.vehicle_repository import VehicleRepository
from app.repositories.mapping_repository import MappingRepository
from app.core.security import verify_token
from app.core.logging import logger, sanitize_sensitive_data
from app.core.exceptions import AuthenticationException


router = APIRouter(tags=["prediction"])


async def get_current_user(authorization: str = Header(None)):
    """
    Verify JWT token from Authorization header.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Token is missing!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1] if " " in authorization else authorization
        payload = verify_token(token)
        return payload
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/predict", response_model=PredictionResponse)
async def predict_price(
    request_data: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Predict vehicle price based on input parameters.
    Main API endpoint maintaining backward compatibility.

    Process:
    1. Validate and normalize input data
    2. Check model exists in mapping
    3. Estimate price using market data
    4. Return prediction with status flag

    Args:
        request_data: Vehicle details (manufacture, model, fuel, transmission, engine_capacity, yom)
        db: Database session
        current_user: Authenticated user from token

    Returns:
        PredictionResponse with predicted price and status

    Raises:
        HTTPException: If validation fails or prediction error occurs
    """
    ct = datetime.now()
    logger.info(f"Prediction request received from user: {current_user.get('user')}")

    try:
        # Sanitize and log request data
        sanitized_request = sanitize_sensitive_data(request_data.model_dump())
        logger.info(f"Request data: {sanitized_request}")

        # Normalize input data
        manufacturer = request_data.manufacture.upper().strip()
        erp_model = request_data.model.upper().strip()
        fuel = request_data.fuel.upper().strip()
        transmission = request_data.transmission.upper().strip()
        engine_capacity = request_data.engine_capacity.upper().strip()
        yom = request_data.yom.strip()

        # Apply transformations
        fuel = ValidationService.change_fuel_type(fuel)
        transmission = ValidationService.change_transmission(transmission)

        # Validate all inputs
        if not ValidationService.validate_all_inputs(
            manufacturer, fuel, transmission, yom, engine_capacity
        ):
            logger.warning("Input validation failed")
            return PredictionResponse(
                flag="input Data is not a valid",
                timestamps=ct,
                Predicted_Price="0",
                host_id=socket.gethostname()
            )

        # Initialize repositories and services
        mapping_repo = MappingRepository(db)
        vehicle_repo = VehicleRepository(db)

        # Check if model exists in mapping
        if not mapping_repo.check_model_exists(manufacturer, erp_model):
            logger.warning(f"Model not in mapped list: {manufacturer} {erp_model}")
            return PredictionResponse(
                flag="model is not a mapped list",
                timestamps=ct,
                Predicted_Price="0",
                host_id=socket.gethostname()
            )

        # Perform price estimation
        logger.info("Starting price estimation")
        prediction_service = PredictionService(vehicle_repo, mapping_repo)
        mean_price, flag = prediction_service.estimate_price(manufacturer, erp_model, yom)

        logger.info(f"Price prediction successful: {mean_price} ({flag})")

        return PredictionResponse(
            flag=flag,
            timestamps=ct,
            Predicted_Price=str(int(mean_price)),
            host_id=socket.gethostname()
        )

    except Exception as e:
        logger.error(f"Error during price prediction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "message": "An error occurred during Price Estimation",
                "host_id": socket.gethostname()
            }
        )
