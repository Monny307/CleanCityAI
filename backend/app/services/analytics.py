from math import hypot

from app.models import WasteReport


def dbscan_reports(reports: list[WasteReport], radius: float = 0.012, minimum_reports: int = 2) -> list[dict]:
    """Cluster report coordinates with a small, dependency-free DBSCAN implementation.

    Coordinates are kept in degrees; radius is deliberately a documented demonstration
    threshold and should be replaced with a projected/PostGIS distance in production.
    """
    points = [(report.latitude, report.longitude) for report in reports]
    visited: set[int] = set()
    clusters: list[list[int]] = []

    def neighbors(index: int) -> list[int]:
        return [candidate for candidate, point in enumerate(points)
                if hypot(point[0] - points[index][0], point[1] - points[index][1]) <= radius]

    for index in range(len(points)):
        if index in visited:
            continue
        visited.add(index)
        nearby = neighbors(index)
        if len(nearby) < minimum_reports:
            continue
        cluster = set(nearby)
        frontier = list(nearby)
        while frontier:
            candidate = frontier.pop()
            if candidate not in visited:
                visited.add(candidate)
                candidate_neighbors = neighbors(candidate)
                if len(candidate_neighbors) >= minimum_reports:
                    frontier.extend(item for item in candidate_neighbors if item not in cluster)
                    cluster.update(candidate_neighbors)
        clusters.append(sorted(cluster))

    results = []
    for cluster in clusters:
        selected = [reports[index] for index in cluster]
        results.append({
            "latitude": sum(report.latitude for report in selected) / len(selected),
            "longitude": sum(report.longitude for report in selected) / len(selected),
            "report_count": len(selected),
            "high_severity_count": sum(report.severity == "high" for report in selected),
            "report_ids": [report.id for report in selected],
        })
    return results


def priority_for_report(report: WasteReport, frequency: int, now_days: float) -> dict:
    severity = {"low": 25, "medium": 60, "high": 100}.get(report.severity, 50)
    frequency_score = min(frequency * 25, 100)
    overdue_score = min(max(now_days, 0) * 10, 100)
    score = round(0.4 * severity + 0.3 * frequency_score + 0.2 * overdue_score + 0.1 * 0, 1)
    level = "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 40 else "low"
    return {"report_id": report.id, "score": score, "level": level, "reasons": ["Population density unavailable; score uses 0 for that component.", f"Severity is {report.severity}."]}
