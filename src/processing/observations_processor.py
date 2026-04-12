from src.data.getter import DatabaseGetter
import logging

logger = logging.getLogger(__name__)

class ObservationProcessor:
    def __init__(self, response_data: list[dict]):
        self.response_data = response_data 

    def get_ready_to_ingest_records(self, records_class):
        records = []
        stations = DatabaseGetter.get_stations()
        stations_ids = [station.station_id for station in stations]
        for observation in self.response_data:
            if observation["geo_id_insee"] in stations_ids:
                records.append(records_class(
                    **{var: val for var, val in observation.items()}
                ))
        if records == [] and stations_ids != []:
            logger.error("The API returned data for the current data but the logic in ObservationProcessor did not handle it correctly")
        return records