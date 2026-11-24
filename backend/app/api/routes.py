from math import hypot
from os import getenv

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models import CollectionPoint, User
from app.security import require_admin

router = APIRouter(prefix="/api/routes", tags=["routes"])


class RouteRequest(BaseModel):
    collection_point_ids: list[int] = Field(min_length=2, max_length=50)
    start_point_id: int | None = None


def osrm_route(points: list[CollectionPoint]) -> dict | None:
    base_url = getenv("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/")
    coordinates = ";".join(f"{point.longitude},{point.latitude}" for point in points)
    try:
        response = httpx.get(
            f"{base_url}/route/v1/driving/{coordinates}",
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "Ok" or not payload.get("routes"):
            return None
        route = payload["routes"][0]
        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "geometry": route["geometry"]["coordinates"],
        }
    except (httpx.HTTPError, KeyError, ValueError):
        return None


@router.post("/optimize")
def optimize(payload: RouteRequest, db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> dict:
    points = list(db.scalars(select(CollectionPoint).where(CollectionPoint.id.in_(payload.collection_point_ids))).all())
    by_id = {point.id: point for point in points}
    if payload.start_point_id is not None and payload.start_point_id not in by_id:
        raise HTTPException(status_code=422, detail="Start point must be one of the selected collection points")
    remaining = [point for point in points]
    first = by_id[payload.start_point_id] if payload.start_point_id is not None else remaining[0]
    remaining.remove(first)
    ordered = [first]
    current = first
    while remaining:
        next_point = min(remaining, key=lambda point: hypot(point.latitude - current.latitude, point.longitude - current.longitude))
        remaining.remove(next_point)
        ordered.append(next_point)
        current = next_point

    def distance(items: list[CollectionPoint]) -> float:
        return round(sum(hypot(items[index].latitude - items[index - 1].latitude,
                              items[index].longitude - items[index - 1].longitude) * 111
                       for index in range(1, len(items))), 2)

    original = [by_id[point_id] for point_id in payload.collection_point_ids if point_id in by_id]
    original_osrm = osrm_route(original)
    optimized_osrm = osrm_route(ordered)
    road_network_available = original_osrm is not None and optimized_osrm is not None
    original_distance = original_osrm["distance_km"] if original_osrm else distance(original)
    optimized_distance = optimized_osrm["distance_km"] if optimized_osrm else distance(ordered)
    saved = round((original_distance - optimized_distance) / original_distance * 100, 1) if original_distance else 0
    return {
        "stop_ids": [point.id for point in ordered],
        "original_distance_km": original_distance,
        "optimized_distance_km": optimized_distance,
        "distance_saved_percent": saved,
        "route_geometry": [[longitude, latitude] for longitude, latitude in optimized_osrm["geometry"]] if optimized_osrm else None,
        "road_network_available": road_network_available,
        "method": "OSRM OpenStreetMap road routing" if road_network_available else "demonstration_coordinate_matrix_nearest_neighbor",
        "routing_disclaimer": ("Road routes use the public OSRM routing service and OpenStreetMap data; no measured fuel or live traffic data." if road_network_available else "Demonstration distance matrix; not a measured road-network or fuel estimate."),
        "created_by": current_user.id,
    }


@router.get("")
def list_routes(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[dict]:
    points = list(db.scalars(select(CollectionPoint)).all())
    return [{"id": point.id, "name": point.name, "latitude": point.latitude, "longitude": point.longitude, "priority_score": point.priority_score} for point in points]
