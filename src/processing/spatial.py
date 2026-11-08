from dataclasses import dataclass
import numpy as np

from src.data.models import SilverObservationListeStationsRecords


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

    The grid axes must be one-dimensional and contain at least one coordinate.
    """
    if grid_lats.ndim != 1 or grid_lons.ndim != 1:
        raise ValueError("Grid latitude and longitude coordinates must be one-dimensional")
    if grid_lats.size == 0 or grid_lons.size == 0:
        raise ValueError("Grid latitude and longitude coordinates cannot be empty")

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
