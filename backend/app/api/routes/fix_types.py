"""REST endpoints for the fix type catalog."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fix import FixTypeCreate, FixTypeRead, FixTypeUpdate
from app.services import fix_types

router = APIRouter(prefix="/fix-types", tags=["fix types"])


@router.get("", response_model=list[FixTypeRead])
def list_fix_types(
    include_inactive: bool = Query(default=False), db: Session = Depends(get_db)
) -> list[FixTypeRead]:
    return fix_types.list_fix_types(db, include_inactive=include_inactive)


@router.post("", response_model=FixTypeRead, status_code=status.HTTP_201_CREATED)
def create_fix_type(data: FixTypeCreate, db: Session = Depends(get_db)) -> FixTypeRead:
    return fix_types.create_fix_type(db, data)


@router.get("/{fix_type_id}", response_model=FixTypeRead)
def get_fix_type(fix_type_id: int, db: Session = Depends(get_db)) -> FixTypeRead:
    return fix_types.get_fix_type(db, fix_type_id)


@router.patch("/{fix_type_id}", response_model=FixTypeRead)
def update_fix_type(
    fix_type_id: int, data: FixTypeUpdate, db: Session = Depends(get_db)
) -> FixTypeRead:
    return fix_types.update_fix_type(db, fix_type_id, data)


@router.delete("/{fix_type_id}", response_model=FixTypeRead)
def deactivate_fix_type(fix_type_id: int, db: Session = Depends(get_db)) -> FixTypeRead:
    return fix_types.deactivate_fix_type(db, fix_type_id)
