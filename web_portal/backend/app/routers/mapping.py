from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..models.mapping import ERPModelMapping
from ..models.audit import AuditLog
from ..schemas.mapping import (
    ERPModelMappingCreate,
    ERPModelMappingUpdate,
    ERPModelMappingResponse,
)
from ..middleware.auth import get_current_user, require_role

router = APIRouter(prefix="/api/mapping", tags=["erp-mapping"])


@router.get("", response_model=List[ERPModelMappingResponse])
async def get_mappings(
    manufacturer: Optional[str] = None,
    erp_name: Optional[str] = None,
    mapped_name: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get ERP model mappings with optional filters."""
    query = db.query(ERPModelMapping)

    if manufacturer:
        query = query.filter(ERPModelMapping.manufacturer.ilike(f"%{manufacturer}%"))
    if erp_name:
        query = query.filter(ERPModelMapping.erp_name.ilike(f"%{erp_name}%"))
    if mapped_name:
        query = query.filter(ERPModelMapping.mapped_name.ilike(f"%{mapped_name}%"))

    mappings = query.offset(skip).limit(limit).all()
    return mappings


@router.post("", response_model=ERPModelMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    mapping: ERPModelMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Create a new ERP model mapping (admin only)."""
    # Check if mapping already exists
    existing = (
        db.query(ERPModelMapping)
        .filter(
            ERPModelMapping.manufacturer == mapping.manufacturer,
            ERPModelMapping.erp_name == mapping.erp_name,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mapping with this manufacturer and ERP name already exists",
        )

    db_mapping = ERPModelMapping(**mapping.model_dump(), updated_by=current_user.id)
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)

    # Log to audit
    audit = AuditLog(
        table_name="erp_model_mapping",
        operation="CREATE",
        user_id=current_user.id,
        new_data=mapping.model_dump(),
    )
    db.add(audit)
    db.commit()

    return db_mapping


@router.put("/{mapping_id}", response_model=ERPModelMappingResponse)
async def update_mapping(
    mapping_id: int,
    mapping: ERPModelMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Update an ERP model mapping (admin only)."""
    db_mapping = db.query(ERPModelMapping).filter(ERPModelMapping.id == mapping_id).first()

    if not db_mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")

    # Store old data for audit
    old_data = {
        "manufacturer": db_mapping.manufacturer,
        "erp_name": db_mapping.erp_name,
        "mapped_name": db_mapping.mapped_name,
    }

    # Update only provided fields
    update_data = mapping.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_mapping, field, value)

    db_mapping.updated_by = current_user.id
    db.commit()
    db.refresh(db_mapping)

    # Log to audit
    audit = AuditLog(
        table_name="erp_model_mapping",
        operation="UPDATE",
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
    )
    db.add(audit)
    db.commit()

    return db_mapping


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Delete an ERP model mapping (admin only)."""
    db_mapping = db.query(ERPModelMapping).filter(ERPModelMapping.id == mapping_id).first()

    if not db_mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")

    # Store data for audit
    old_data = {
        "manufacturer": db_mapping.manufacturer,
        "erp_name": db_mapping.erp_name,
        "mapped_name": db_mapping.mapped_name,
    }

    db.delete(db_mapping)

    # Log to audit
    audit = AuditLog(
        table_name="erp_model_mapping",
        operation="DELETE",
        user_id=current_user.id,
        old_data=old_data,
    )
    db.add(audit)
    db.commit()
