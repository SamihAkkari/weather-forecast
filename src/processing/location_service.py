from src.data import queries
from src.data.models import SilverObservationListeStationsRecords
from src.processing.spatial import find_nearest_station


def get_nearest_station(
    lat: float,
    lng: float,
) -> SilverObservationListeStationsRecords:
    stations = queries.get_stations()
    return find_nearest_station(stations, lat, lng)
