from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(StrEnum):
    CITIZEN = "citizen"
    ADMIN = "admin"


class ReportStatus(StrEnum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    SCHEDULED = "scheduled"
    COLLECTED = "collected"
    REJECTED = "rejected"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.CITIZEN.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reports: Mapped[list["WasteReport"]] = relationship(back_populates="reporter")


class WasteReport(Base):
    __tablename__ = "waste_reports"
    __table_args__ = (
        Index("ix_waste_reports_location", "latitude", "longitude"),
        Index("ix_waste_reports_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    image_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default=ReportStatus.PENDING.value, index=True)
    severity: Mapped[str] = mapped_column(String(20), default=Severity.MEDIUM.value)
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    reporter: Mapped[User] = relationship(back_populates="reports")
    status_history: Mapped[list["ReportStatusHistory"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("waste_reports.id"), index=True)
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report: Mapped[WasteReport] = relationship(back_populates="status_history")


class WasteCategory(Base):
    __tablename__ = "waste_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)


class Hotspot(Base):
    __tablename__ = "hotspots"

    id: Mapped[int] = mapped_column(primary_key=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    report_count: Mapped[int] = mapped_column(Integer)
    severity_score: Mapped[float] = mapped_column(Float)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CollectionPoint(Base):
    __tablename__ = "collection_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    priority_score: Mapped[float] = mapped_column(Float, default=0)


class CollectionRoute(Base):
    __tablename__ = "collection_routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    total_distance_km: Mapped[float] = mapped_column(Float, default=0)
    optimized_distance_km: Mapped[float] = mapped_column(Float, default=0)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RouteStop(Base):
    __tablename__ = "route_stops"

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("collection_routes.id"), index=True)
    collection_point_id: Mapped[int] = mapped_column(ForeignKey("collection_points.id"))
    stop_order: Mapped[int] = mapped_column(Integer)


class OpenDataSource(Base):
    __tablename__ = "open_data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    url: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    format: Mapped[str] = mapped_column(String(80))
    license: Mapped[str] = mapped_column(String(160))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
