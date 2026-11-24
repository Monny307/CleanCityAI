from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WasteReport
from app.schemas import ReportResponse
from app.security import require_admin
from app.services.ai_analysis import analyze_image
from app.services.analytics import dbscan_reports, priority_for_report

router = APIRouter(tags=["intelligence"])


@router.post("/api/ai/analyze")
async def analyze(file: UploadFile = File(...), _: User = Depends(require_admin)) -> dict:
    return analyze_image(file.filename)


@router.post("/api/ai/classify")
async def classify(file: UploadFile = File(...), _: User = Depends(require_admin)) -> dict:
    return analyze_image(file.filename)


@router.get("/api/hotspots")
def hotspots(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[dict]:
    reports = list(db.scalars(select(WasteReport).where(WasteReport.status != "rejected")).all())
    return dbscan_reports(reports)


@router.post("/api/hotspots/detect")
def detect_hotspots(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    reports = list(db.scalars(select(WasteReport).where(WasteReport.status != "rejected")).all())
    clusters = dbscan_reports(reports)
    return {"clusters": clusters, "minimum_evidence": 2, "method": "DBSCAN"}


@router.get("/api/priorities")
def priorities(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[dict]:
    reports = list(db.scalars(select(WasteReport).where(WasteReport.status != "collected")).all())
    frequency = {}
    for report in reports:
        key = (round(report.latitude, 3), round(report.longitude, 3))
        frequency[key] = frequency.get(key, 0) + 1
    now = datetime.now(timezone.utc)
    return [
        priority_for_report(report, frequency[(round(report.latitude, 3), round(report.longitude, 3))],
                            (now - report.created_at).total_seconds() / 86400 if report.created_at else 0)
        for report in reports
    ]
