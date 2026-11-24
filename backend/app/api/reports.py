import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReportStatusHistory, User, WasteReport
from app.schemas import ReportCreate, ReportResponse, ReportStatusUpdate
from app.security import get_current_user, require_admin

router = APIRouter(prefix="/api/reports", tags=["reports"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    category: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    severity: str = Form("medium"),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WasteReport:
    if not 11.4 <= latitude <= 11.7 or not 104.7 <= longitude <= 105.1:
        raise HTTPException(status_code=422, detail="Coordinates must be within the Phnom Penh pilot area")
    if severity not in {"low", "medium", "high"}:
        raise HTTPException(status_code=422, detail="Invalid severity")

    image_url = None
    if image is not None:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=422, detail="Upload a JPEG, PNG, or WebP image")
        extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[image.content_type]
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = UPLOAD_DIR / filename
        size = 0
        with destination.open("wb") as target:
            while chunk := image.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_IMAGE_BYTES:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")
                target.write(chunk)
        image_url = f"/api/uploads/{filename}"

    report = WasteReport(
        reporter_id=current_user.id,
        category=category,
        description=description,
        latitude=latitude,
        longitude=longitude,
        severity=severity,
        image_url=image_url,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=list[ReportResponse])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_status: str | None = None,
) -> list[WasteReport]:
    query = select(WasteReport).order_by(WasteReport.created_at.desc())
    if current_user.role != "admin":
        query = query.where(WasteReport.reporter_id == current_user.id)
    if report_status:
        query = query.where(WasteReport.status == report_status)
    return list(db.scalars(query).all())


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> WasteReport:
    report = db.get(WasteReport, report_id)
    if report is None or (current_user.role != "admin" and report.reporter_id != current_user.id):
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}/status", response_model=ReportResponse)
def update_status(
    report_id: int,
    payload: ReportStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> WasteReport:
    report = db.get(WasteReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = payload.status
    db.add(ReportStatusHistory(report_id=report.id, changed_by_id=current_user.id, status=payload.status, note=payload.note))
    db.commit()
    db.refresh(report)
    return report
