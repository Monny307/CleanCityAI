# CleanCity AI

CleanCity AI is a smart waste-management platform for Phnom Penh. It connects citizen waste reports with AI-assisted classification, geospatial hotspot detection, priority scoring, and route optimization for collection teams.

## Architecture

```text
React + Vite + TypeScript + Tailwind
            |
        REST/JSON
            |
FastAPI + Pydantic + SQLAlchemy
            |
PostgreSQL + PostGIS
            |
AI service | DBSCAN hotspots | priority scoring | OR-Tools routes
```

The initial implementation is intentionally a thin vertical slice: the frontend is runnable, the backend exposes a versioned health endpoint, and the boundaries for the domain services and data layers are in place. This lets subsequent stages add authentication, reports, analytics, and optimization without replacing the foundation.

## Project layout

- `frontend/` - React client and dashboard shell
- `backend/` - FastAPI application
- `data/raw/` and `data/processed/` - external data import stages
- `docs/` - architecture and data-source documentation
- `docker-compose.yml` - local PostgreSQL/PostGIS service

## Run locally

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Backend

Once Python 3.11+ is installed (use `py` on Windows if `python` is not on PATH):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with Swagger UI at `/docs`.

### Database

```powershell
docker compose up -d db
```

Copy `.env.example` to `.env` before connecting the backend to PostgreSQL.

## Development seed account

The authentication and seed implementation is now available. After starting PostgreSQL and installing backend dependencies, run:

```powershell
cd backend
python seed.py
```

Demo accounts:

- Administrator: `admin@cleancity-ai.com` / `CleanCityDemo2026!`
- Citizen: `citizen@cleancity-ai.com` / `CleanCityDemo2026!`

These are development-only credentials and must be changed before deployment.

### Development database fallback

Docker/PostgreSQL is the production-style target. If Docker or valid local PostgreSQL credentials are unavailable, copy the following into `backend/.env` for a development-only SQLite database:

```text
DATABASE_URL=sqlite:///./cleancity.db
```

SQLite mode is not a substitute for PostGIS and should not be used for production deployment.

