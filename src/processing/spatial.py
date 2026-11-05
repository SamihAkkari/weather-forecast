import numpy as np
from dataclasses import dataclass
import xarray as xr
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
    station_id : int
    lat_nearest_grid_idx : int
    lon_nearest_grid_idx : int

def find_nearest_station(stations: list[SilverObservationListeStationsRecords], lat: float, long: float) -> SilverObservationListeStationsRecords:
    min_distance = float('inf')
    nearest_station = None

    for station in stations:
        distance = np.sqrt((station.latitude - lat) ** 2 + (station.longitude - long) ** 2)
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    return nearest_station

def find_nearest_grid_indices(
    stations  : list[dict],
    grid_lats,       # 1D array of grid latitudes
    grid_lons,      # 1D array of grid longitudes
) -> list[StationNearestGrid]:
    """
    Vectorized nearest-neighbour lookup on a regular lat/lon grid.
    Pure spatial logic   no variable or schema knowledge.
    """
    lats = np.array([s.latitude  for s in stations])
    lons = np.array([s.longitude for s in stations])

    lat_idxs = np.abs(grid_lats[:, None] - lats[None, :]).argmin(axis=0)
    lon_idxs = np.abs(grid_lons[:, None] - lons[None, :]).argmin(axis=0)

    # closest_grid_lats = grid_lats[lat_idxs]
    # closest_grid_lons = grid_lons[lon_idxs]
    return [
        StationNearestGrid(s.station_id, lat_idxs[i], lon_idxs[i])
        for i, s in enumerate(stations)
    ]


def extract_at_indices(
    da      : xr.DataArray,
    indices : list[StationNearestGrid],
) -> np.ndarray:
    """
    params:
    -------
        da: (n_steps, n_lat, n_lon)
        indices: list of (station_id, lat_idx, lon_idx)
    returns:
    -------
        array of shape (n_stations, n_steps) with values extracted at the given lat/lon indices for each time step.
    
    logic:
        Extract (n_stations, n_steps) array from a (n_steps, n_lat, n_lon) DataArray.
    """
    lat_idxs = np.array([idx.lat_nearest_grid_idx for idx in indices])
    lon_idxs = np.array([idx.lon_nearest_grid_idx for idx in indices])
    
    return da[:, lat_idxs, lon_idxs].T  # (n_stations, n_steps)

