from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models.user import User
from ..models.vehicle import FastMovingVehicle, ScrapedVehicle
from ..models.mapping import ERPModelMapping
from ..models.audit import AuditLog
from ..middleware.auth import get_current_user
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_fast_moving: int
    total_scraped: int
    total_mappings: int
    recent_updates_count: int
    total_users: int


class PricePoint(BaseModel):
    date: datetime
    price: float


class PriceMovementResponse(BaseModel):
    manufacturer: str
    model: str
    yom: int
    price_history: List[PricePoint]
    avg_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    trend: Optional[str]  # "increasing", "decreasing", "stable"


class ModelYearOption(BaseModel):
    manufacturer: str
    model: str
    year: int
    label: str


class FastMovingIndexRequest(BaseModel):
    days: int = 90
    data_source: str = "fast_moving"
    vehicle_type: Optional[str] = None
    models: List[ModelYearOption] = []


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics."""
    from ..models.user import User as UserModel

    total_fast_moving = db.query(func.count(FastMovingVehicle.id)).scalar()
    total_scraped = db.query(func.count(ScrapedVehicle.id)).scalar()
    total_mappings = db.query(func.count(ERPModelMapping.id)).scalar()
    total_users = db.query(func.count(UserModel.id)).scalar()

    # Get updates from last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_updates = db.query(func.count(AuditLog.id)).filter(AuditLog.timestamp >= seven_days_ago).scalar()

    return {
        "total_fast_moving": total_fast_moving or 0,
        "total_scraped": total_scraped or 0,
        "total_mappings": total_mappings or 0,
        "recent_updates_count": recent_updates or 0,
        "total_users": total_users or 0,
    }


@router.get("/price-movement", response_model=PriceMovementResponse)
async def get_price_movement(
    manufacturer: str,
    model: str,
    yom: int,
    days: int = Query(90, ge=1, le=36500),
    data_source: str = Query("fast_moving", regex="^(fast_moving|scraped)$"),
    vehicle_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get price movement data for a specific vehicle from selected data source."""
    start_date = datetime.utcnow() - timedelta(days=days)

    if data_source == "fast_moving":
        # Query fast moving vehicles for price history based on user-specified date
        query = db.query(FastMovingVehicle).filter(
            and_(
                FastMovingVehicle.manufacturer == manufacturer,
                FastMovingVehicle.model == model,
                FastMovingVehicle.yom == yom,
                FastMovingVehicle.date >= start_date,
                FastMovingVehicle.price.isnot(None),
            )
        )

        # Add vehicle type filter if specified
        if vehicle_type:
            query = query.filter(FastMovingVehicle.type == vehicle_type)

        vehicles = query.order_by(FastMovingVehicle.date).all()

        if not vehicles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No price history found for this vehicle",
            )

        # Extract price points using the user-specified date field
        price_history = [{"date": v.date, "price": float(v.price)} for v in vehicles]
    else:
        # Query scraped vehicles for price history
        query = db.query(ScrapedVehicle).filter(
            and_(
                ScrapedVehicle.manufacturer == manufacturer,
                ScrapedVehicle.model == model,
                ScrapedVehicle.yom == yom,
                ScrapedVehicle.updated_date >= start_date,
                ScrapedVehicle.price.isnot(None),
            )
        )

        # Add vehicle type filter if specified
        if vehicle_type:
            query = query.filter(ScrapedVehicle.type == vehicle_type)

        vehicles = query.order_by(ScrapedVehicle.updated_date).all()

        if not vehicles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No price history found for this vehicle",
            )

        # Extract price points using the updated_date field
        price_history = [{"date": v.updated_date, "price": float(v.price)} for v in vehicles]

    # Calculate statistics
    prices = [float(v.price) for v in vehicles]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    # Determine trend
    trend = "stable"
    if len(prices) >= 2:
        first_half = prices[: len(prices) // 2]
        second_half = prices[len(prices) // 2 :]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_second > avg_first * 1.05:  # 5% increase
            trend = "increasing"
        elif avg_second < avg_first * 0.95:  # 5% decrease
            trend = "decreasing"

    return {
        "manufacturer": manufacturer,
        "model": model,
        "yom": yom,
        "price_history": price_history,
        "avg_price": round(avg_price, 2),
        "min_price": min_price,
        "max_price": max_price,
        "trend": trend,
    }


@router.post("/fast-moving-index", response_model=PriceMovementResponse)
async def get_fast_moving_index(
    request: FastMovingIndexRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate Fast Moving Vehicle Index based on user-selected vehicle components."""
    start_date = datetime.utcnow() - timedelta(days=request.days)

    # Use user-selected models if provided, otherwise use default index components
    if request.models and len(request.models) > 0:
        # Convert user-selected models to index components format
        index_components = [(model.model, model.year) for model in request.models]
    else:
        # Define default index components: (model_pattern, year)
        index_components = [
            ("WAGON R", 2017),      # Wagon R Stringrey 2017
            ("vezel", 2017),        # Vezel 2017
            ("Premio", 2018),       # Premio 2018
            ("Aqua", 2015),         # Aqua 2015
            ("axio", 2018),         # Axio WXB 2018
        ]

    if request.data_source == "fast_moving":
        # Get all distinct dates in the range
        dates_query = db.query(FastMovingVehicle.date).distinct().filter(
            and_(
                FastMovingVehicle.date >= start_date,
                FastMovingVehicle.price.isnot(None),
            )
        )
        if request.vehicle_type:
            dates_query = dates_query.filter(FastMovingVehicle.type == request.vehicle_type)

        distinct_dates = dates_query.order_by(FastMovingVehicle.date).all()
        distinct_dates = [d[0] for d in distinct_dates]

        if not distinct_dates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data found for the selected time range",
            )

        # Calculate index value for each date
        price_history = []
        for date_obj in distinct_dates:
            index_value = 0
            component_count = 0

            for model_pattern, year in index_components:
                # Query average price for this component on this date
                query = db.query(func.avg(FastMovingVehicle.price)).filter(
                    and_(
                        FastMovingVehicle.yom == year,
                        FastMovingVehicle.model.ilike(f"%{model_pattern}%"),
                        FastMovingVehicle.date == date_obj,
                        FastMovingVehicle.price.isnot(None),
                    )
                )
                if request.vehicle_type:
                    query = query.filter(FastMovingVehicle.type == request.vehicle_type)

                avg_price = query.scalar()

                if avg_price:
                    index_value += float(avg_price)
                    component_count += 1

            if component_count > 0:
                price_history.append({
                    "date": date_obj,
                    "price": round(index_value, 2)
                })

        if not price_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No index data available for the selected criteria",
            )

        # Calculate statistics
        prices = [p["price"] for p in price_history]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)

        # Determine trend
        trend = "stable"
        if len(prices) >= 2:
            first_half = prices[: len(prices) // 2]
            second_half = prices[len(prices) // 2 :]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)

            if avg_second > avg_first * 1.05:
                trend = "increasing"
            elif avg_second < avg_first * 0.95:
                trend = "decreasing"

        return {
            "manufacturer": "Fast Moving Vehicle Index",
            "model": "",
            "yom": 0,
            "price_history": price_history,
            "avg_price": round(avg_price, 2),
            "min_price": min_price,
            "max_price": max_price,
            "trend": trend,
        }
    else:
        # Scraped data doesn't support index calculation
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Index calculation is only available for Fast Moving Vehicle Data",
        )


@router.get("/manufacturers")
async def get_manufacturers(
    data_source: str = Query("fast_moving", regex="^(fast_moving|scraped)$"),
    vehicle_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of unique manufacturers from selected data source."""
    if data_source == "fast_moving":
        query = db.query(FastMovingVehicle.manufacturer).distinct()
        if vehicle_type:
            query = query.filter(FastMovingVehicle.type == vehicle_type)
        manufacturers = query.all()
    else:
        query = db.query(ScrapedVehicle.manufacturer).distinct()
        if vehicle_type:
            query = query.filter(ScrapedVehicle.type == vehicle_type)
        manufacturers = query.all()

    return [m[0] for m in manufacturers if m[0]]


@router.get("/models")
async def get_models(
    manufacturer: Optional[str] = None,
    data_source: str = Query("fast_moving", regex="^(fast_moving|scraped)$"),
    vehicle_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of unique models from selected data source, optionally filtered by manufacturer."""
    if data_source == "fast_moving":
        query = db.query(FastMovingVehicle.model).distinct()
        if manufacturer:
            query = query.filter(FastMovingVehicle.manufacturer == manufacturer)
        if vehicle_type:
            query = query.filter(FastMovingVehicle.type == vehicle_type)
        models = query.all()
    else:
        query = db.query(ScrapedVehicle.model).distinct()
        if manufacturer:
            query = query.filter(ScrapedVehicle.manufacturer == manufacturer)
        if vehicle_type:
            query = query.filter(ScrapedVehicle.type == vehicle_type)
        models = query.all()

    return [m[0] for m in models if m[0]]


@router.get("/years")
async def get_years(
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    data_source: str = Query("fast_moving", regex="^(fast_moving|scraped)$"),
    vehicle_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of unique years from selected data source, optionally filtered by manufacturer and model."""
    if data_source == "fast_moving":
        query = db.query(FastMovingVehicle.yom).distinct()
        if manufacturer:
            query = query.filter(FastMovingVehicle.manufacturer == manufacturer)
        if model:
            query = query.filter(FastMovingVehicle.model == model)
        if vehicle_type:
            query = query.filter(FastMovingVehicle.type == vehicle_type)
        years = query.order_by(FastMovingVehicle.yom.desc()).all()
    else:
        query = db.query(ScrapedVehicle.yom).distinct()
        if manufacturer:
            query = query.filter(ScrapedVehicle.manufacturer == manufacturer)
        if model:
            query = query.filter(ScrapedVehicle.model == model)
        if vehicle_type:
            query = query.filter(ScrapedVehicle.type == vehicle_type)
        years = query.order_by(ScrapedVehicle.yom.desc()).all()

    return [y[0] for y in years if y[0]]


@router.get("/all-model-years")
async def get_all_model_years(
    data_source: str = Query("fast_moving", regex="^(fast_moving|scraped)$"),
    vehicle_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all unique model-year combinations from selected data source."""
    if data_source == "fast_moving":
        query = db.query(
            FastMovingVehicle.manufacturer,
            FastMovingVehicle.model,
            FastMovingVehicle.yom
        ).distinct()
        if vehicle_type:
            query = query.filter(FastMovingVehicle.type == vehicle_type)
        combinations = query.order_by(
            FastMovingVehicle.manufacturer,
            FastMovingVehicle.model,
            FastMovingVehicle.yom.desc()
        ).all()
    else:
        query = db.query(
            ScrapedVehicle.manufacturer,
            ScrapedVehicle.model,
            ScrapedVehicle.yom
        ).distinct()
        if vehicle_type:
            query = query.filter(ScrapedVehicle.type == vehicle_type)
        combinations = query.order_by(
            ScrapedVehicle.manufacturer,
            ScrapedVehicle.model,
            ScrapedVehicle.yom.desc()
        ).all()

    # Format the response
    result = []
    for manufacturer, model, year in combinations:
        if manufacturer and model and year:
            result.append({
                "manufacturer": manufacturer,
                "model": model,
                "year": year,
                "label": f"{manufacturer} {model} ({year})"
            })

    return result
