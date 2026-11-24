# CleanCity AI architecture

## Boundaries

- **Frontend**: page routing, forms, map and chart presentation, API client, role-aware navigation.
- **API**: authentication, request validation, report lifecycle, dashboard queries, and orchestration of domain services.
- **Domain services**: image analysis, DBSCAN hotspot detection, priority scoring, and OR-Tools route optimization remain isolated from HTTP handlers.
- **Persistence**: SQLAlchemy models and migrations target PostgreSQL with PostGIS geometry columns and spatial indexes.
- **Data pipeline**: raw downloads are immutable; processed datasets are normalized before import and linked to documented sources.

## Implementation sequence

1. Foundation and vertical health slice (current stage).
2. Database models, migrations, demo seed data, and authentication.
3. Citizen report submission and administrator report management.
4. AI analysis interface with an explicitly labeled baseline model.
5. Hotspot detection and priority scoring.
6. Route optimization and map visualization.
7. Open-data import workflow, analytics, testing, and deployment hardening.

