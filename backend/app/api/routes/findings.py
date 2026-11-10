"""REST endpoints for diagnostic finding records."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.finding import FindingCreate, FindingRead, FindingUpdate
from app.services import findings

router = APIRouter(tags=["findings"])


@router.get("/diagnostics/{diagnostic_id}/findings", response_model=list[FindingRead])
def list_findings(diagnostic_id: int, db: Session = Depends(get_db)) -> list[FindingRead]:
    return findings.list_findings(db, diagnostic_id)


@router.post(
    "/diagnostics/{diagnostic_id}/findings",
    response_model=FindingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_finding(
    diagnostic_id: int, data: FindingCreate, db: Session = Depends(get_db)
) -> FindingRead:
    return findings.create_finding(db, diagnostic_id, data)


@router.get("/findings/{finding_id}", response_model=FindingRead)
def get_finding(finding_id: int, db: Session = Depends(get_db)) -> FindingRead:
    return findings.get_finding(db, finding_id)


@router.patch("/findings/{finding_id}", response_model=FindingRead)
def update_finding(
    finding_id: int, data: FindingUpdate, db: Session = Depends(get_db)
) -> FindingRead:
    return findings.update_finding(db, finding_id, data)


@router.delete("/findings/{finding_id}", response_model=FindingRead)
def archive_finding(finding_id: int, db: Session = Depends(get_db)) -> FindingRead:
    return findings.archive_finding(db, finding_id)
