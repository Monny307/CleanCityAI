from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReportStatus, User, WasteReport
from app.schemas import AnalyticsResponse, CategoryCount, DashboardSummary
from app.security import require_admin

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> DashboardSummary:
    total = db.scalar(select(func.count(WasteReport.id))) or 0
    pending = db.scalar(select(func.count(WasteReport.id)).where(WasteReport.status.in_([ReportStatus.PENDING.value, ReportStatus.UNDER_REVIEW.value]))) or 0
    completed = db.scalar(select(func.count(WasteReport.id)).where(WasteReport.status == ReportStatus.COLLECTED.value)) or 0
    critical = db.scalar(select(func.count(WasteReport.id)).where(WasteReport.severity == "high", WasteReport.status != ReportStatus.COLLECTED.value)) or 0
    return DashboardSummary(total_reports=total, pending_reports=pending, critical_hotspots=critical, high_priority_locations=critical, completed_collections=completed)


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> AnalyticsResponse:
    reports = list(db.scalars(select(WasteReport).order_by(WasteReport.created_at)).all())
    categories = Counter(report.category for report in reports)
    statuses = Counter(report.status for report in reports)
    dates = Counter(report.created_at.strftime("%Y-%m-%d") for report in reports if report.created_at)
    return AnalyticsResponse(
        reports_by_category=[CategoryCount(category=key, count=value) for key, value in categories.items()],
        reports_by_status=[CategoryCount(category=key, count=value) for key, value in statuses.items()],
        reports_over_time=[CategoryCount(category=key, count=value) for key, value in sorted(dates.items())],
    )
