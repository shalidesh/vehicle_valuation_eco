from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any
from datetime import datetime
from ..database import get_db
from ..models.user import User
from ..models.vehicle import FastMovingVehicle, ScrapedVehicle
from ..models.mapping import ERPModelMapping
from ..models.audit import AuditLog
from ..middleware.auth import require_role
from pydantic import BaseModel

router = APIRouter(prefix="/api/bulk-upload", tags=["bulk-upload"])


class BulkUploadRequest(BaseModel):
    table_name: str
    data: List[Dict[str, Any]]


class ValidationError(BaseModel):
    row: int
    column: str
    message: str


class BulkUploadResponse(BaseModel):
    success: bool
    message: str
    inserted: int
    duplicates: int
    errors: List[ValidationError]


def normalize_text(value: Any) -> Any:
    """Convert text values to uppercase."""
    if isinstance(value, str) and value.strip():
        return value.strip().upper()
    return value


def validate_and_prepare_fast_moving_vehicle(data: Dict[str, Any], row_num: int) -> tuple:
    """Validate and prepare fast moving vehicle data."""
    errors = []

    # Required fields
    required_fields = ['type', 'manufacturer', 'model', 'yom']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(ValidationError(
                row=row_num,
                column=field,
                message=f"Missing required field: {field}"
            ))

    if errors:
        return None, errors

    # Prepare data with normalized text
    prepared = {
        'type': normalize_text(data.get('type')),
        'manufacturer': normalize_text(data.get('manufacturer')),
        'model': normalize_text(data.get('model')),
        'yom': int(data.get('yom')),
        'price': float(data.get('price')) if data.get('price') else None,
        'date': datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.now(),
    }

    return prepared, []


def validate_and_prepare_scraped_vehicle(data: Dict[str, Any], row_num: int) -> tuple:
    """Validate and prepare scraped vehicle data."""
    errors = []

    # Required fields
    required_fields = ['type', 'manufacturer', 'model', 'yom']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(ValidationError(
                row=row_num,
                column=field,
                message=f"Missing required field: {field}"
            ))

    if errors:
        return None, errors

    # Prepare data with normalized text
    prepared = {
        'type': normalize_text(data.get('type')),
        'manufacturer': normalize_text(data.get('manufacturer')),
        'model': normalize_text(data.get('model')),
        'yom': int(data.get('yom')),
        'transmission': normalize_text(data.get('transmission')) if data.get('transmission') else None,
        'fuel_type': normalize_text(data.get('fuel_type')) if data.get('fuel_type') else None,
        'mileage': int(data.get('mileage')) if data.get('mileage') else None,
        'price': float(data.get('price')) if data.get('price') else None,
    }

    return prepared, []


def validate_and_prepare_erp_mapping(data: Dict[str, Any], row_num: int) -> tuple:
    """Validate and prepare ERP mapping data."""
    errors = []

    # Required fields
    required_fields = ['manufacturer', 'erp_name', 'mapped_name']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(ValidationError(
                row=row_num,
                column=field,
                message=f"Missing required field: {field}"
            ))

    if errors:
        return None, errors

    # Prepare data with normalized text
    prepared = {
        'manufacturer': normalize_text(data.get('manufacturer')),
        'erp_name': normalize_text(data.get('erp_name')),
        'mapped_name': normalize_text(data.get('mapped_name')),
    }

    return prepared, []


def check_fast_moving_duplicate(db: Session, data: Dict[str, Any]) -> bool:
    """Check if fast moving vehicle record already exists."""
    existing = db.query(FastMovingVehicle).filter(
        FastMovingVehicle.type == data['type'],
        FastMovingVehicle.manufacturer == data['manufacturer'],
        FastMovingVehicle.model == data['model'],
        FastMovingVehicle.yom == data['yom'],
        FastMovingVehicle.date == data['date'],
    ).first()
    return existing is not None


def check_scraped_duplicate(db: Session, data: Dict[str, Any]) -> bool:
    """Check if scraped vehicle record already exists (allow multiple entries for same vehicle)."""
    # For scraped vehicles, we don't check for duplicates as the same vehicle
    # can be scraped multiple times with different prices/dates
    return False


def check_erp_mapping_duplicate(db: Session, data: Dict[str, Any]) -> bool:
    """Check if ERP mapping already exists."""
    existing = db.query(ERPModelMapping).filter(
        ERPModelMapping.manufacturer == data['manufacturer'],
        ERPModelMapping.erp_name == data['erp_name'],
    ).first()
    return existing is not None


@router.post("", response_model=BulkUploadResponse)
async def bulk_upload(
    request: BulkUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """
    Bulk upload CSV data to database tables (admin only).

    Supports:
    - fast_moving_vehicles
    - scraped_vehicles
    - erp_model_mappings

    Features:
    - Validates required columns
    - Converts text to uppercase
    - Ignores duplicates
    - All-or-nothing: If ANY validation errors exist, NO records are inserted
    - Returns detailed upload statistics
    """
    table_name = request.table_name
    data = request.data

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided"
        )

    # Select validation and duplicate check functions based on table
    if table_name == "fast_moving_vehicles":
        model_class = FastMovingVehicle
        validate_func = validate_and_prepare_fast_moving_vehicle
        check_duplicate_func = check_fast_moving_duplicate
    elif table_name == "scraped_vehicles":
        model_class = ScrapedVehicle
        validate_func = validate_and_prepare_scraped_vehicle
        check_duplicate_func = check_scraped_duplicate
    elif table_name == "erp_model_mappings":
        model_class = ERPModelMapping
        validate_func = validate_and_prepare_erp_mapping
        check_duplicate_func = check_erp_mapping_duplicate
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported table: {table_name}"
        )

    validation_errors = []
    prepared_records = []
    duplicate_count = 0

    # PHASE 1: Validate ALL records first (don't insert anything yet)
    for idx, row in enumerate(data, start=1):
        # Validate and prepare data
        prepared_data, errors = validate_func(row, idx)

        if errors:
            validation_errors.extend(errors)
            continue

        # Check for duplicates
        if check_duplicate_func(db, prepared_data):
            duplicate_count += 1
            continue

        # Add updated_by for tables that support it
        if table_name in ["fast_moving_vehicles", "erp_model_mappings"]:
            prepared_data['updated_by'] = current_user.id

        prepared_records.append(prepared_data)

    # If there are ANY validation errors, abort and return errors
    if validation_errors:
        # Log failed attempt to audit
        audit = AuditLog(
            table_name=table_name,
            operation="BULK_UPLOAD_FAILED",
            user_id=current_user.id,
            new_data={
                "total_records": len(data),
                "validation_errors": len(validation_errors),
                "reason": "Validation errors prevented upload",
            },
        )
        db.add(audit)
        db.commit()

        return BulkUploadResponse(
            success=False,
            message=f"Upload aborted. {len(validation_errors)} validation error(s) found. Please fix all errors and try again.",
            inserted=0,
            duplicates=duplicate_count,
            errors=validation_errors,
        )

    # PHASE 2: If validation passed, insert all records in a transaction
    inserted_count = 0

    try:
        for prepared_data in prepared_records:
            db_record = model_class(**prepared_data)
            db.add(db_record)
            inserted_count += 1

        # Commit all records at once
        db.commit()
    except IntegrityError as e:
        db.rollback()
        validation_errors.append(ValidationError(
            row=0,
            column="",
            message=f"Database integrity error: {str(e)}"
        ))
        inserted_count = 0
    except Exception as e:
        db.rollback()
        validation_errors.append(ValidationError(
            row=0,
            column="",
            message=f"Database error: {str(e)}"
        ))
        inserted_count = 0

    # Log to audit
    audit = AuditLog(
        table_name=table_name,
        operation="BULK_UPLOAD",
        user_id=current_user.id,
        new_data={
            "inserted": inserted_count,
            "duplicates": duplicate_count,
            "errors": len(validation_errors),
            "total_records": len(data),
        },
    )
    db.add(audit)
    db.commit()

    # Determine success status
    success = inserted_count > 0 and len(validation_errors) == 0

    if inserted_count == 0 and len(validation_errors) == 0:
        message = f"All {duplicate_count} records were duplicates. No new records inserted."
    elif inserted_count > 0:
        message = f"Successfully inserted {inserted_count} records."
        if duplicate_count > 0:
            message += f" Skipped {duplicate_count} duplicates."
        if validation_errors:
            message += f" {len(validation_errors)} records had errors."
    else:
        message = f"Upload failed. {len(validation_errors)} validation errors."

    return BulkUploadResponse(
        success=success,
        message=message,
        inserted=inserted_count,
        duplicates=duplicate_count,
        errors=validation_errors,
    )
