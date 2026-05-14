from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.finding import Finding
from app.models.scan import Scan
from app.schemas.guardrail import (
    FindingRead,
    MetricsResponse,
    ScanCreateResponse,
    ScanDetailRead,
    ScanRead,
)
from app.services import metrics_service, scan_service

router = APIRouter(tags=["guardrail"])


@router.post("/scan", response_model=ScanCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    db: Session = Depends(get_db),
    name: str | None = Form(default=None),
    files: list[UploadFile] = File(...),
) -> ScanCreateResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    payloads: list[tuple[str, str]] = []
    for upload in files:
        raw = await upload.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"File {upload.filename!r} must be UTF-8 encoded text.",
            ) from exc
        payloads.append((upload.filename or "upload.tf", text))

    try:
        scan = scan_service.run_scan_from_text_files(db, name, payloads)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ScanCreateResponse(scan=ScanRead.model_validate(scan))


@router.get("/scans", response_model=list[ScanDetailRead])
def list_scans(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> list[ScanDetailRead]:
    rows = db.execute(select(Scan).order_by(Scan.created_at.desc()).offset(offset).limit(limit)).scalars().all()
    out: list[ScanDetailRead] = []
    for row in rows:
        n = db.scalar(select(func.count()).select_from(Finding).where(Finding.scan_id == row.id)) or 0
        data = ScanRead.model_validate(row).model_dump()
        data["finding_count"] = int(n)
        out.append(ScanDetailRead(**data))
    return out


@router.get("/findings", response_model=list[FindingRead])
def list_findings(
    db: Session = Depends(get_db),
    scan_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[FindingRead]:
    stmt = select(Finding)
    if scan_id is not None:
        stmt = stmt.where(Finding.scan_id == scan_id)
    stmt = stmt.order_by(Finding.created_at.desc()).offset(offset).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [FindingRead.model_validate(r) for r in rows]


@router.get("/findings/{finding_id}", response_model=FindingRead)
def get_finding(finding_id: int, db: Session = Depends(get_db)) -> FindingRead:
    row = db.get(Finding, finding_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Finding not found.")
    return FindingRead.model_validate(row)


@router.get("/metrics", response_model=MetricsResponse)
def read_metrics(db: Session = Depends(get_db)) -> MetricsResponse:
    return metrics_service.get_metrics(db)


@router.delete("/scan/{scan_id}")
def remove_scan(scan_id: int, db: Session = Depends(get_db)) -> Response:
    if not scan_service.delete_scan(db, scan_id):
        raise HTTPException(status_code=404, detail="Scan not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)