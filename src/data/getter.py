
from src.config.config import Config
from src.data.db import DatabaseConnection
from src.data.models import ObservationListeStationsRecords
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

class DatabaseGetter:


    @staticmethod
    def transform_list_of_objects_to_list_of_dict(data: List[object]):
        """
        data: is a tuble of list of tuples, where each tuple is a row from the observation table in the database
        
        returns
        -------
            List of dictionaries where each dictionary is a row in the data
        """
        results = []
        for obj in data:
            results.append(obj.__dict__)
        return results

    @staticmethod
    def transform_data_to_list_of_dict(data: List[Tuple], cur):
        """
        data: is a tuble of list of tuples, where each tuple is a row from the observation table in the database
        cur: is teh cursor returned when fetching this data
        
        returns
        -------
            List of dictionaries where each dictionary is a row in the data
        """
        columns = [desc[0] for desc in cur.description]
        result = []
        for row in data:
            record = dict(zip(columns, row))
            for key, value in record.items():
                if hasattr(value, "isoformat"):  # datetime
                    record[key] = value.isoformat()
            result.append(record)
        return result
        
    @staticmethod
    def get_formatted_observations(station_id, fromm, time = None):
        row_data, cur = DatabaseGetter.get_observations(station_id, fromm, time)
        data = DatabaseGetter.transform_data_to_list_of_dict(row_data, cur)
        return data
   
    @staticmethod
    def get_formatted_forecasts(station_id, fromm, time = None, exactly_at_time = False):
        row_data, cur = DatabaseGetter.get_forecasts(station_id, fromm, time, exactly_at_time)
        data = DatabaseGetter.transform_data_to_list_of_dict(row_data, cur)
        return data

    @staticmethod
    def get_frontend_formatted_data_for_basicV(station_id, time = None, obs_table_name = None):
        """
        time: is the current time when the request is send from the backend
        """
        if obs_table_name is None:
            obs_fromm = Config.OBSERVATIONS_TABLE_NAME_HOURLY
        else:
            obs_fromm = Config.OBSERVATIONS_TABLE_NAME_6m
        current_observation = DatabaseGetter.get_formatted_observations(station_id = station_id, fromm = obs_fromm, time = time)
        
        if len(current_observation) > 1:
            logger.error("Current observation for a station should be exactly one record in the data, however, more than one record was found")
            raise ValueError()
        
        if len(current_observation) == 0 or len(current_observation) > 1:
            current_observation = [0] #quick fix
            logger.warning("Current observation for a station should be exactly one record in the data, however, no records were found, now I force a zero value")
        
        forecasts = DatabaseGetter.get_formatted_forecasts(station_id = station_id, fromm = Config.FORECAST_TABLE_NAME, time = time, exactly_at_time = False)
        data = {"conditions" : current_observation[0],
                "forecast" : forecasts}
        return data

    @staticmethod
    def get_observations(station_id, fromm, time = None):
        # if "6m" in fromm:
        #     dataclass_obj = ObservationInfrahoraire6mRecord
        # else:
        #     dataclass_obj = ObservationHoraireRecord

        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                if time is None:
                    cur.execute(f"""
                            SELECT * 
                            FROM {Config.SILVER_SCHEMA}.{fromm}
                            WHERE
                                station_id = %s 
                            """, (station_id,))
                else:
                    cur.execute(f"""
                            SELECT * 
                            FROM {Config.SILVER_SCHEMA}.{fromm}
                            WHERE
                                station_id = %s and time_step_fr = %s
                            
                            """, (station_id,time,))
                return cur.fetchall(), cur

    @staticmethod
    def get_forecasts(station_id, fromm, time = None, exactly_at_time = False):
        if exactly_at_time:
            condition = "="
        else:
            condition = ">"

        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                if time is None:
                    cur.execute(f"""
                            SELECT DISTINCT ON (station_id, time_step_fr) *
                            FROM {Config.SILVER_SCHEMA}.{fromm}
                            WHERE 
                                station_id = %s
                            ORDER BY station_id, time_step_fr, run_time DESC;
                                """, (station_id,))
                else:
                    cur.execute(f"""
                            SELECT DISTINCT ON (station_id, time_step_fr) *
                            FROM {Config.SILVER_SCHEMA}.{fromm}
                            WHERE 
                                station_id = %s AND time_step_fr {condition} %s
                            ORDER BY station_id, time_step_fr, run_time DESC;
                                """, (station_id, time,))
                return cur.fetchall(), cur


    @staticmethod
    def get_stations() -> list[ObservationListeStationsRecords]:
        cols = ', '.join(ObservationListeStationsRecords.columns()) 
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT {cols}
                        FROM {Config.BRONZE_SCHEMA}.{Config.STATIONS_TABLE_NAME}
                        ORDER BY station_id
                    """)
                    return [
                        ObservationListeStationsRecords(*row)   
                        for row in cur.fetchall()
                    ]
        
        except Exception as e:
            logger.error(f"Error fetching stations: {e}")
            raise

    @staticmethod
    def get_stations_to_show_on_map_in_basicV():
        raw_stations= DatabaseGetter.get_stations()
        stations = DatabaseGetter.transform_list_of_objects_to_list_of_dict(raw_stations)
        return stations