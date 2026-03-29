from src.data.getter import DatabaseGetter

class ObservationProcessor:
    def __init__(self, response_data: list[dict]):
        self.response_data = response_data 

    def get_ready_to_ingest_records(self, records_class):
        records = []
        import pdb
        pdb.set_trace()
        stations = DatabaseGetter.get_stations()
        stations_ids = [station.station_id for station in stations]
        for observation in self.response_data:
            if int(observation["geo_id_insee"]) in stations_ids:
                records.append(records_class(
                    **{var: val for var, val in observation.items()}
                ))
        return records