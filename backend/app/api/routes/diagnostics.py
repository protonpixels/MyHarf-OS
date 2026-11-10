"""REST endpoints for website diagnostic records."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.diagnostic import DiagnosticCreate, DiagnosticRead, DiagnosticUpdate
from app.services import diagnostics

router = APIRouter(tags=["diagnostics"])


@router.get("/customers/{customer_id}/diagnostics", response_model=list[DiagnosticRead])
def list_diagnostics(customer_id: int, db: Session = Depends(get_db)) -> list[DiagnosticRead]:
    return diagnostics.list_diagnostics(db, customer_id)


@router.post(
    "/customers/{customer_id}/diagnostics",
    response_model=DiagnosticRead,
    status_code=status.HTTP_201_CREATED,
)
def create_diagnostic(
    customer_id: int, data: DiagnosticCreate, db: Session = Depends(get_db)
) -> DiagnosticRead:
    return diagnostics.create_diagnostic(db, customer_id, data)


@router.get("/diagnostics/{diagnostic_id}", response_model=DiagnosticRead)
def get_diagnostic(diagnostic_id: int, db: Session = Depends(get_db)) -> DiagnosticRead:
    return diagnostics.get_diagnostic(db, diagnostic_id)


@router.patch("/diagnostics/{diagnostic_id}", response_model=DiagnosticRead)
def update_diagnostic(
    diagnostic_id: int, data: DiagnosticUpdate, db: Session = Depends(get_db)
) -> DiagnosticRead:
    return diagnostics.update_diagnostic(db, diagnostic_id, data)


@router.delete("/diagnostics/{diagnostic_id}", response_model=DiagnosticRead)
def archive_diagnostic(diagnostic_id: int, db: Session = Depends(get_db)) -> DiagnosticRead:
    return diagnostics.archive_diagnostic(db, diagnostic_id)
