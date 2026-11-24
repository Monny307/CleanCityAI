from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ReportCreate(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    description: str = Field(min_length=5, max_length=2000)
    latitude: float = Field(ge=11.4, le=11.7)
    longitude: float = Field(ge=104.7, le=105.1)
    severity: str = Field(default="medium", pattern="^(low|medium|high)$")
    image_url: str | None = None


class ReportStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|under_review|scheduled|collected|rejected)$")
    note: str | None = Field(default=None, max_length=500)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    description: str
    latitude: float
    longitude: float
    image_url: str | None
    status: str
    severity: str
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    reporter_id: int


class DashboardSummary(BaseModel):
    total_reports: int
    pending_reports: int
    critical_hotspots: int
    high_priority_locations: int
    completed_collections: int


class CategoryCount(BaseModel):
    category: str
    count: int


class AnalyticsResponse(BaseModel):
    reports_by_category: list[CategoryCount]
    reports_by_status: list[CategoryCount]
    reports_over_time: list[CategoryCount]
