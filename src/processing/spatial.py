import numpy as np
from dataclasses import dataclass
from src.data.models import SilverObservationListeStationsRecords

import json
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.prepared import prep


class GeoUtils:

    _france_polygon = None

    @classmethod
    def _load_france_polygon(cls):
        """Load and cache the metropolitan France boundary."""
        if cls._france_polygon is None:
            path = Path(__file__).parent / "france_metropole.geojson"

            with path.open(encoding="utf-8") as file:
                geojson = json.load(file)

            cls._france_polygon = prep(shape(geojson))

        return cls._france_polygon

    @classmethod
    def is_inside_france(cls, latitude: float, longitude: float) -> bool:
        """
        Check whether coordinates are inside metropolitan France.

        Boundary points are considered inside.
        """
        if not (-90 <= latitude <= 90):
            raise ValueError("Invalid latitude")

        if not (-180 <= longitude <= 180):
            raise ValueError("Invalid longitude")

        france = cls._load_france_polygon()

        return france.covers(Point(longitude, latitude))


@dataclass
class StationNearestGrid:
    station_id: str
    lat_nearest_grid_idx: int
    lon_nearest_grid_idx: int


def find_nearest_station(
    stations: list[SilverObservationListeStationsRecords],
    lat: float,
    long: float,
) -> SilverObservationListeStationsRecords:
    min_distance = float('inf')
    nearest_station = None

    for station in stations:
        distance = np.sqrt((station.latitude - lat) ** 2 + (station.longitude - long) ** 2)
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    return nearest_station


def find_nearest_grid_indices(
    stations: list[SilverObservationListeStationsRecords],
    grid_lats: np.ndarray,
    grid_lons: np.ndarray,
) -> list[StationNearestGrid]:
    """
    Find each station's nearest latitude and longitude grid indices.
    """
    lats = np.array([station.latitude for station in stations])
    lons = np.array([station.longitude for station in stations])

    lat_idxs = np.abs(grid_lats[:, None] - lats[None, :]).argmin(axis=0)
    lon_idxs = np.abs(grid_lons[:, None] - lons[None, :]).argmin(axis=0)

    return [
        StationNearestGrid(station.station_id, lat_idxs[index], lon_idxs[index])
        for index, station in enumerate(stations)
    ]


def extract_at_indices(
    da: np.ndarray,
    indices: list[StationNearestGrid],
) -> np.ndarray:
    """
    Extract an array of shape (n_stations, n_steps) from (n_steps, n_lat, n_lon).
    """
    lat_idxs = np.array([idx.lat_nearest_grid_idx for idx in indices])
    lon_idxs = np.array([idx.lon_nearest_grid_idx for idx in indices])

    return da[:, lat_idxs, lon_idxs].T
