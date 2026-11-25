from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.settings import settings
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.reports import router as reports_router
from app.api.intelligence import router as intelligence_router
from app.api.routes import router as routes_router
from app.api.open_data import router as open_data_router

app = FastAPI(
    title="CleanCity AI API",
    description="Waste-management intelligence platform for Phnom Penh.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
app.include_router(intelligence_router)
app.include_router(routes_router)
app.include_router(open_data_router)

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="report-uploads")


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cleancity-api", "version": app.version}

@app.get("/")
def root():
    return {
        "message": "Welcome to CleanCityAI API",
        "status": "running"
    }

