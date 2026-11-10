"""Fix type catalog persistence and business operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fix_type import FixType
from app.schemas.fix import FixTypeCreate, FixTypeUpdate
from app.services.errors import ResourceNotFoundError


def list_fix_types(db: Session, *, include_inactive: bool = False) -> list[FixType]:
    statement = select(FixType).order_by(FixType.id)
    if not include_inactive:
        statement = statement.where(FixType.status == "active")
    return list(db.scalars(statement))


def get_fix_type(db: Session, fix_type_id: int) -> FixType:
    fix_type = db.get(FixType, fix_type_id)
    if fix_type is None:
        raise ResourceNotFoundError("Fix type not found")
    return fix_type


def create_fix_type(db: Session, data: FixTypeCreate) -> FixType:
    fix_type = FixType(**data.model_dump())
    db.add(fix_type)
    db.commit()
    db.refresh(fix_type)
    return fix_type


def update_fix_type(db: Session, fix_type_id: int, data: FixTypeUpdate) -> FixType:
    fix_type = get_fix_type(db, fix_type_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fix_type, field, value)
    db.commit()
    db.refresh(fix_type)
    return fix_type


def deactivate_fix_type(db: Session, fix_type_id: int) -> FixType:
    fix_type = get_fix_type(db, fix_type_id)
    fix_type.status = "inactive"
    db.commit()
    db.refresh(fix_type)
    return fix_type
