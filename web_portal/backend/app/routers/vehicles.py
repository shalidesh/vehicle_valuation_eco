from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..models.vehicle import FastMovingVehicle, ScrapedVehicle
from ..models.audit import AuditLog
from ..schemas.vehicle import (
    FastMovingVehicleCreate,
    FastMovingVehicleUpdate,
    FastMovingVehicleResponse,
    ScrapedVehicleCreate,
    ScrapedVehicleUpdate,
    ScrapedVehicleResponse,
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


# Scraped Vehicles Endpoints
@router.get("/scraped", response_model=List[ScrapedVehicleResponse])
async def get_scraped_vehicles(
    vehicle_type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    yom: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get scraped vehicles with optional filters."""
    query = db.query(ScrapedVehicle)

    if vehicle_type:
        query = query.filter(ScrapedVehicle.type == vehicle_type)
    if manufacturer:
        query = query.filter(ScrapedVehicle.manufacturer.ilike(f"%{manufacturer}%"))
    if model:
        query = query.filter(ScrapedVehicle.model.ilike(f"%{model}%"))
    if yom:
        query = query.filter(ScrapedVehicle.yom == yom)

    # Order by updated_date (most recent first)
    vehicles = query.order_by(ScrapedVehicle.updated_date.desc()).offset(skip).limit(limit).all()
    return vehicles


@router.post("/scraped", response_model=ScrapedVehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_scraped_vehicle(
    vehicle: ScrapedVehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Create a new scraped vehicle entry (admin only)."""
    db_vehicle = ScrapedVehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)

    # Log to audit
    new_data = vehicle.model_dump()
    # Convert Decimal to float for JSON serialization
    if new_data.get("price") is not None:
        new_data["price"] = float(new_data["price"])

    audit = AuditLog(
        table_name="scraped_vehicles",
        operation="CREATE",
        user_id=current_user.id,
        new_data=new_data,
    )
    db.add(audit)
    db.commit()

    return db_vehicle


@router.put("/scraped/{vehicle_id}", response_model=ScrapedVehicleResponse)
async def update_scraped_vehicle(
    vehicle_id: int,
    vehicle: ScrapedVehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Update a scraped vehicle entry (admin only)."""
    db_vehicle = db.query(ScrapedVehicle).filter(ScrapedVehicle.id == vehicle_id).first()

    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Store old data for audit
    old_data = {
        "type": db_vehicle.type,
        "manufacturer": db_vehicle.manufacturer,
        "model": db_vehicle.model,
        "yom": db_vehicle.yom,
        "transmission": db_vehicle.transmission,
        "fuel_type": db_vehicle.fuel_type,
        "mileage": db_vehicle.mileage,
        "price": float(db_vehicle.price) if db_vehicle.price else None,
    }

    # Update only provided fields
    update_data = vehicle.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)

    db.commit()
    db.refresh(db_vehicle)

    # Convert Decimal to float for JSON serialization in update_data
    audit_update_data = update_data.copy()
    if audit_update_data.get("price") is not None:
        audit_update_data["price"] = float(audit_update_data["price"])

    # Log to audit
    audit = AuditLog(
        table_name="scraped_vehicles",
        operation="UPDATE",
        user_id=current_user.id,
        old_data=old_data,
        new_data=audit_update_data,
    )
    db.add(audit)
    db.commit()

    return db_vehicle


@router.delete("/scraped/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scraped_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Delete a scraped vehicle entry (admin only)."""
    db_vehicle = db.query(ScrapedVehicle).filter(ScrapedVehicle.id == vehicle_id).first()

    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Store data for audit
    old_data = {
        "type": db_vehicle.type,
        "manufacturer": db_vehicle.manufacturer,
        "model": db_vehicle.model,
        "yom": db_vehicle.yom,
        "transmission": db_vehicle.transmission,
        "fuel_type": db_vehicle.fuel_type,
        "mileage": db_vehicle.mileage,
        "price": float(db_vehicle.price) if db_vehicle.price else None,
    }

    db.delete(db_vehicle)

    # Log to audit
    audit = AuditLog(
        table_name="scraped_vehicles",
        operation="DELETE",
        user_id=current_user.id,
        old_data=old_data,
    )
    db.add(audit)
    db.commit()
