from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import CollectionPoint, User, WasteCategory, WasteReport
from app.security import hash_password

DEMO_COORDINATES = [
    (11.5564, 104.9282), (11.5621, 104.9160), (11.5487, 104.9345),
    (11.5682, 104.9027), (11.5354, 104.9217), (11.5758, 104.9341),
    (11.5441, 104.9118), (11.5902, 104.9170), (11.5288, 104.9501),
    (11.5588, 104.9459), (11.5397, 104.8995), (11.5804, 104.9570),
    (11.5502, 104.8874), (11.5181, 104.9290), (11.5710, 104.9235),
]
CATEGORIES = ["household", "plastic", "construction", "illegal_dumping", "food", "mixed"]
SEVERITIES = ["low", "medium", "high"]


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        legacy_admin = db.scalar(select(User).where(User.email == "admin@cleancity.local"))
        if legacy_admin is not None:
            legacy_admin.email = "admin@cleancity-ai.com"
        legacy_citizen = db.scalar(select(User).where(User.email == "citizen@cleancity.local"))
        if legacy_citizen is not None:
            legacy_citizen.email = "citizen@cleancity-ai.com"
        admin = db.scalar(select(User).where(User.email == "admin@cleancity-ai.com"))
        if admin is None:
            admin = User(
                email="admin@cleancity-ai.com",
                password_hash=hash_password("CleanCityDemo2026!"),
                full_name="CleanCity Administrator",
                role="admin",
            )
            db.add(admin)
            db.flush()

        citizen = db.scalar(select(User).where(User.email == "citizen@cleancity-ai.com"))
        if citizen is None:
            citizen = User(
                email="citizen@cleancity-ai.com",
                password_hash=hash_password("CleanCityDemo2026!"),
                full_name="Demo Citizen",
            )
            db.add(citizen)
            db.flush()

        for category in CATEGORIES:
            if db.scalar(select(WasteCategory).where(WasteCategory.name == category)) is None:
                db.add(WasteCategory(name=category))

        if db.query(CollectionPoint).count() == 0:
            for index, (latitude, longitude) in enumerate(DEMO_COORDINATES[:6]):
                db.add(CollectionPoint(name=f"Demo collection point {index + 1}", latitude=latitude, longitude=longitude, priority_score=80 - index * 7))

        existing_demo_count = db.query(WasteReport).filter(WasteReport.is_demo.is_(True)).count()
        if existing_demo_count == 0:
            now = datetime.now(timezone.utc)
            for index, (latitude, longitude) in enumerate(DEMO_COORDINATES):
                db.add(WasteReport(
                    reporter_id=citizen.id,
                    category=CATEGORIES[index % len(CATEGORIES)],
                    description=f"Simulated Phnom Penh demonstration report #{index + 1}",
                    latitude=latitude,
                    longitude=longitude,
                    status=["pending", "under_review", "scheduled", "collected"][index % 4],
                    severity=SEVERITIES[index % len(SEVERITIES)],
                    is_demo=True,
                    created_at=now - timedelta(days=index * 2),
                ))
        db.commit()
    print("Seeded demo accounts, categories, and 15 reports.")


if __name__ == "__main__":
    seed()
