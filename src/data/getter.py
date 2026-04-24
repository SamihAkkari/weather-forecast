
from src.config.config import Config
from src.data.db import DatabaseConnection
from src.data.models import SilverObservationListeStationsRecords, SilverForecastAromeRecords
import logging
from typing import Tuple, List
from datetime import datetime
import src.processing.analysis_processor as analysis

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
        row_data, cur = DatabaseGetter.get_forecasts_at_time_step(station_id, fromm, time, exactly_at_time)
        data = DatabaseGetter.transform_data_to_list_of_dict(row_data, cur)
        return data

    @staticmethod
    def get_frontend_formatted_data_for_basicV(station, time = None, obs_table_name = None):
        """
        time: is the current time when the request is send from the backend
        """
        if obs_table_name is None:
            obs_fromm = Config.OBSERVATIONS_TABLE_NAME_HOURLY
        else:
            obs_fromm = Config.OBSERVATIONS_TABLE_NAME_6m
        current_observation = DatabaseGetter.get_formatted_observations(station_id = station.station_id, fromm = obs_fromm, time = time)
        
        if len(current_observation) > 1:
            logger.error("Current observation for a station should be exactly one record in the data, however, more than one record was found")
            raise ValueError()
        
        if len(current_observation) == 0 or len(current_observation) > 1:
            current_observation = [0] #quick fix
            logger.warning("Current observation for a station should be exactly one record in the data, however, no records were found, now I force a zero value")
        
        forecasts = DatabaseGetter.get_formatted_forecasts(station_id = station.station_id, fromm = Config.SILVER_FORECAST_AROME_TABLE_NAME, time = time, exactly_at_time = False)
        data = {
            "station_info" : station.__dict__,
            "conditions" : current_observation[0],
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
                    if isinstance(time, tuple):
                        if len(time) != 2:
                            logger.error("time if provided as a tuple it should contain two values")
                            raise ValueError
                        if time[1] < time[0]:
                            logger.error("Invalid time ranges")
                            raise ValueError
                        cur.execute(f"""
                                SELECT * 
                                FROM {Config.SILVER_SCHEMA}.{fromm}
                                WHERE
                                    station_id = %s and time_step_fr > %s and time_step_fr < %s
                                """, (station_id,time[0],time[1]))
                    elif isinstance(time, datetime):
                        cur.execute(f"""
                                SELECT * 
                                FROM {Config.SILVER_SCHEMA}.{fromm}
                                WHERE
                                    station_id = %s and time_step_fr = %s
                                
                                """, (station_id,time,))
                    else:
                        logger.error("In get_observations, the time should either be None to get all observations of the station, or a tuple to get a range of time, or datetime to get at specific timestep, other types are not handled")
                        raise ValueError
                return cur.fetchall(), cur


    @staticmethod
    def get_forecast_run(station_id, fromm, run_time):
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                if run_time is None:
                    logger.error("run_time should not be None")
                    raise ValueError
                else:
                    cur.execute(f"""
                            SELECT DISTINCT ON (station_id, time_step_fr) *
                            FROM {Config.SILVER_SCHEMA}.{fromm}
                            WHERE 
                                station_id = %s AND run_time = %s
                            ORDER BY station_id, time_step_fr, run_time DESC;
                                """, (station_id, run_time,))
                    return [
                        SilverForecastAromeRecords(*row)   
                        for row in cur.fetchall()
                    ]
                
                
                # return cur.fetchall(), cur

    @staticmethod
    def get_forecasts_at_time_step(station_id, fromm, time = None, exactly_at_time = False):
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
    def get_stations() -> list[SilverObservationListeStationsRecords]:
        cols = ', '.join(SilverObservationListeStationsRecords.columns()) 
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT {cols}
                        FROM {Config.SILVER_SCHEMA}.{Config.STATIONS_TABLE_NAME}
                        ORDER BY station_id
                    """)
                    return [
                        SilverObservationListeStationsRecords(*row)   
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
    
    @staticmethod
    def get_frontend_formatted_data_for_analysis(station, run_time):
        # Step 1 - Get forecast data
        forecast_data = DatabaseGetter.get_forecast_run(station.station_id, Config.SILVER_FORECAST_AROME_TABLE_NAME, run_time)
        time_range = (forecast_data[0].time_step_fr, forecast_data[-1].time_step_fr)
        
        # Step 2 — fetch observations for the same time window
        observations_data, cur = DatabaseGetter.get_observations(
            station.station_id, Config.OBSERVATIONS_TABLE_NAME_HOURLY, time_range
        )

        analysis.compute(
            DatabaseGetter.transform_list_of_objects_to_list_of_dict(forecast_data),
            DatabaseGetter.transform_data_to_list_of_dict(observations_data, cur)
            )
        
        
        

