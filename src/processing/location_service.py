from src.data.getter import DatabaseGetter
from src.data.models import SilverObservationListeStationsRecords
from src.processing.spatial import find_nearest_station


def get_nearest_station(
    lat: float,
    lng: float,
) -> SilverObservationListeStationsRecords:
    stations = DatabaseGetter.get_stations()
    return find_nearest_station(stations, lat, lng)
