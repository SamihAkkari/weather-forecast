import json
from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.prepared import prep


@lru_cache(maxsize=1)
def _metropolitan_france_boundary():
    path = Path(__file__).with_name("france_metropole.geojson")
    with path.open(encoding="utf-8") as file:
        geojson = json.load(file)
    return prep(shape(geojson))


def is_inside_metropolitan_france(latitude: float, longitude: float) -> bool:
    """Return whether coordinates are within metropolitan France."""
    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude")
    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude")

    return _metropolitan_france_boundary().covers(Point(longitude, latitude))
