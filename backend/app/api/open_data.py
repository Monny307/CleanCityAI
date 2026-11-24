from fastapi import APIRouter

router = APIRouter(prefix="/api/open-data", tags=["open data"])

SOURCES = [
    {"name": "OpenStreetMap", "url": "https://www.openstreetmap.org/", "purpose": "Map and road context", "license": "ODbL", "status": "configured source"},
    {"name": "Geofabrik Cambodia", "url": "https://download.geofabrik.de/asia/cambodia.html", "purpose": "Cambodia OSM extracts", "license": "ODbL", "status": "import workflow pending"},
    {"name": "WorldPop", "url": "https://www.worldpop.org/", "purpose": "Population density", "license": "Dataset-specific", "status": "import workflow pending"},
    {"name": "Open Development Cambodia", "url": "https://data.opendevelopmentcambodia.net/", "purpose": "Environmental context", "license": "Dataset-specific", "status": "import workflow pending"},
    {"name": "Humanitarian Data Exchange", "url": "https://data.humdata.org/", "purpose": "Administrative boundaries", "license": "Dataset-specific", "status": "import workflow pending"},
]


@router.get("/sources")
def sources() -> list[dict]:
    return SOURCES
