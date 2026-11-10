"""Finding persistence and business operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.diagnostic import Diagnostic
from app.models.finding import Finding
from app.schemas.finding import FindingCreate, FindingUpdate
from app.services.errors import ResourceConflictError, ResourceNotFoundError


def list_findings(db: Session, diagnostic_id: int) -> list[Finding]:
    if db.get(Diagnostic, diagnostic_id) is None:
        raise ResourceNotFoundError("Diagnostic not found")
    statement = select(Finding).where(Finding.diagnostic_id == diagnostic_id).order_by(Finding.id)
    return list(db.scalars(statement))


def get_finding(db: Session, finding_id: int) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise ResourceNotFoundError("Finding not found")
    return finding


def create_finding(db: Session, diagnostic_id: int, data: FindingCreate) -> Finding:
    diagnostic = db.get(Diagnostic, diagnostic_id)
    if diagnostic is None:
        raise ResourceNotFoundError("Diagnostic not found")
    if diagnostic.status == "archived":
        raise ResourceConflictError("Cannot add findings to an archived diagnostic")
    finding = Finding(
        diagnostic_id=diagnostic_id,
        title=data.title,
        description=data.description,
        page_url=str(data.page_url) if data.page_url is not None else None,
        evidence=data.evidence,
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


def update_finding(db: Session, finding_id: int, data: FindingUpdate) -> Finding:
    finding = get_finding(db, finding_id)
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(finding, field, str(value) if field == "page_url" else value)
    db.commit()
    db.refresh(finding)
    return finding


def archive_finding(db: Session, finding_id: int) -> Finding:
    finding = get_finding(db, finding_id)
    finding.status = "archived"
    db.commit()
    db.refresh(finding)
    return finding
