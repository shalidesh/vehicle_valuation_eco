from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..models.vehicle import FastMovingVehicle, SummaryStatistic
from ..models.audit import AuditLog
from ..schemas.vehicle import (
    FastMovingVehicleCreate,
    FastMovingVehicleUpdate,
    FastMovingVehicleResponse,
    SummaryStatisticCreate,
    SummaryStatisticUpdate,
    SummaryStatisticResponse,
)
from ..middleware.auth import get_current_user, require_role

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


# Fast Moving Vehicles Endpoints
@router.get("/fast-moving", response_model=List[FastMovingVehicleResponse])
async def get_fast_moving_vehicles(
    vehicle_type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    yom: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get fast moving vehicles with optional filters."""
    query = db.query(FastMovingVehicle)

    if vehicle_type:
        query = query.filter(FastMovingVehicle.type == vehicle_type)
    if manufacturer:
        query = query.filter(FastMovingVehicle.manufacturer.ilike(f"%{manufacturer}%"))
    if model:
        query = query.filter(FastMovingVehicle.model.ilike(f"%{model}%"))
    if yom:
        query = query.filter(FastMovingVehicle.yom == yom)

    # Order by date (most recent first)
    vehicles = query.order_by(FastMovingVehicle.date.desc()).offset(skip).limit(limit).all()
    return vehicles


@router.post("/fast-moving", response_model=FastMovingVehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_fast_moving_vehicle(
    vehicle: FastMovingVehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """Create a new fast moving vehicle entry."""
    # Check if vehicle with the same date already exists
    existing = (
        db.query(FastMovingVehicle)
        .filter(
            FastMovingVehicle.type == vehicle.type,
            FastMovingVehicle.manufacturer == vehicle.manufacturer,
            FastMovingVehicle.model == vehicle.model,
            FastMovingVehicle.yom == vehicle.yom,
            FastMovingVehicle.date == vehicle.date,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A price entry for this vehicle on this date already exists",
        )

    db_vehicle = FastMovingVehicle(**vehicle.model_dump(), updated_by=current_user.id)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)

    # Log to audit
    new_data = vehicle.model_dump()
    # Convert Decimal to float for JSON serialization
    if new_data.get("price") is not None:
        new_data["price"] = float(new_data["price"])
    # Convert datetime to ISO string for JSON serialization
    if new_data.get("date") is not None:
        new_data["date"] = new_data["date"].isoformat()

    audit = AuditLog(
        table_name="fast_moving_vehicles",
        operation="CREATE",
        user_id=current_user.id,
        new_data=new_data,
    )
    db.add(audit)
    db.commit()

    return db_vehicle


@router.put("/fast-moving/{vehicle_id}", response_model=FastMovingVehicleResponse)
async def update_fast_moving_vehicle(
    vehicle_id: int,
    vehicle: FastMovingVehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """Update a fast moving vehicle entry."""
    db_vehicle = db.query(FastMovingVehicle).filter(FastMovingVehicle.id == vehicle_id).first()

    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Store old data for audit
    old_data = {
        "type": db_vehicle.type,
        "manufacturer": db_vehicle.manufacturer,
        "model": db_vehicle.model,
        "yom": db_vehicle.yom,
        "price": float(db_vehicle.price) if db_vehicle.price else None,
        "date": db_vehicle.date.isoformat() if db_vehicle.date else None,
    }

    # Update only provided fields
    update_data = vehicle.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)

    db_vehicle.updated_by = current_user.id
    db.commit()
    db.refresh(db_vehicle)

    # Convert Decimal to float and datetime to ISO string for JSON serialization
    audit_update_data = update_data.copy()
    if audit_update_data.get("price") is not None:
        audit_update_data["price"] = float(audit_update_data["price"])
    if audit_update_data.get("date") is not None:
        audit_update_data["date"] = audit_update_data["date"].isoformat()

    # Log to audit
    audit = AuditLog(
        table_name="fast_moving_vehicles",
        operation="UPDATE",
        user_id=current_user.id,
        old_data=old_data,
        new_data=audit_update_data,
    )
    db.add(audit)
    db.commit()

    return db_vehicle


@router.delete("/fast-moving/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fast_moving_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """Delete a fast moving vehicle entry."""
    db_vehicle = db.query(FastMovingVehicle).filter(FastMovingVehicle.id == vehicle_id).first()

    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Store data for audit
    old_data = {
        "type": db_vehicle.type,
        "manufacturer": db_vehicle.manufacturer,
        "model": db_vehicle.model,
        "yom": db_vehicle.yom,
        "price": float(db_vehicle.price) if db_vehicle.price else None,
        "date": db_vehicle.date.isoformat() if db_vehicle.date else None,
    }

    db.delete(db_vehicle)

    # Log to audit
    audit = AuditLog(
        table_name="fast_moving_vehicles",
        operation="DELETE",
        user_id=current_user.id,
        old_data=old_data,
    )
    db.add(audit)
    db.commit()


# Summary Statistics Endpoints
@router.get("/summary-statistics", response_model=List[SummaryStatisticResponse])
async def get_summary_statistics(
    make: Optional[str] = None,
    model: Optional[str] = None,
    yom: Optional[str] = None,
    transmission: Optional[str] = None,
    fuel_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary statistics with optional filters."""
    query = db.query(SummaryStatistic)

    if make:
        query = query.filter(SummaryStatistic.make.ilike(f"%{make}%"))
    if model:
        query = query.filter(SummaryStatistic.model.ilike(f"%{model}%"))
    if yom:
        query = query.filter(SummaryStatistic.yom == yom)
    if transmission:
        query = query.filter(SummaryStatistic.transmission == transmission)
    if fuel_type:
        query = query.filter(SummaryStatistic.fuel_type == fuel_type)

    records = query.order_by(SummaryStatistic.make, SummaryStatistic.model).offset(skip).limit(limit).all()
    return records


@router.post("/summary-statistics", response_model=SummaryStatisticResponse, status_code=status.HTTP_201_CREATED)
async def create_summary_statistic(
    record: SummaryStatisticCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Create a new summary statistic entry (admin only)."""
    # Check for composite PK duplicate
    existing = (
        db.query(SummaryStatistic)
        .filter(
            SummaryStatistic.make == record.make,
            SummaryStatistic.model == record.model,
            SummaryStatistic.yom == record.yom,
            SummaryStatistic.transmission == record.transmission,
            SummaryStatistic.fuel_type == record.fuel_type,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A summary statistic with this combination already exists",
        )

    db_record = SummaryStatistic(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    audit = AuditLog(
        table_name="summery_statistics_table",
        operation="CREATE",
        user_id=current_user.id,
        new_data=record.model_dump(),
    )
    db.add(audit)
    db.commit()

    return db_record


@router.put("/summary-statistics", response_model=SummaryStatisticResponse)
async def update_summary_statistic(
    make: str = Query(...),
    model: str = Query(...),
    yom: str = Query(...),
    transmission: str = Query(...),
    fuel_type: str = Query(...),
    record: SummaryStatisticUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Update a summary statistic entry by composite key (admin only)."""
    db_record = (
        db.query(SummaryStatistic)
        .filter(
            SummaryStatistic.make == make,
            SummaryStatistic.model == model,
            SummaryStatistic.yom == yom,
            SummaryStatistic.transmission == transmission,
            SummaryStatistic.fuel_type == fuel_type,
        )
        .first()
    )

    if not db_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary statistic not found")

    old_data = {
        "make": db_record.make,
        "model": db_record.model,
        "yom": db_record.yom,
        "transmission": db_record.transmission,
        "fuel_type": db_record.fuel_type,
        "average_price": db_record.average_price,
        "updated_date": db_record.updated_date,
    }

    update_data = record.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_record, field, value)

    db.commit()
    db.refresh(db_record)

    audit = AuditLog(
        table_name="summery_statistics_table",
        operation="UPDATE",
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
    )
    db.add(audit)
    db.commit()

    return db_record


@router.delete("/summary-statistics", status_code=status.HTTP_204_NO_CONTENT)
async def delete_summary_statistic(
    make: str = Query(...),
    model: str = Query(...),
    yom: str = Query(...),
    transmission: str = Query(...),
    fuel_type: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Delete a summary statistic entry by composite key (admin only)."""
    db_record = (
        db.query(SummaryStatistic)
        .filter(
            SummaryStatistic.make == make,
            SummaryStatistic.model == model,
            SummaryStatistic.yom == yom,
            SummaryStatistic.transmission == transmission,
            SummaryStatistic.fuel_type == fuel_type,
        )
        .first()
    )

    if not db_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary statistic not found")

    old_data = {
        "make": db_record.make,
        "model": db_record.model,
        "yom": db_record.yom,
        "transmission": db_record.transmission,
        "fuel_type": db_record.fuel_type,
        "average_price": db_record.average_price,
        "updated_date": db_record.updated_date,
    }

    db.delete(db_record)

    audit = AuditLog(
        table_name="summery_statistics_table",
        operation="DELETE",
        user_id=current_user.id,
        old_data=old_data,
    )
    db.add(audit)
    db.commit()
