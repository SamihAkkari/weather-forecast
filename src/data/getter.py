
from src.config.config import Config
from src.data.db import DatabaseConnection
from src.data.models import SilverObservationListeStationsRecords, SilverForecastAromeRecords
import logging
from typing import Tuple, List
from datetime import datetime
import src.processing.analysis_processor as analyser
from src.ingestion.time_manager import TimeManager
from datetime import date, datetime, timedelta
from datetime import date, datetime, time, timedelta
logger = logging.getLogger(__name__)

import time
_STATIONS_CACHE = {"ts": 0.0, "rows": None}

class DatabaseGetter:


    @staticmethod
    def get_full_table(schema: str, table_name: str) -> list[dict]:
        """
        Read all rows from a table in a specified schema.
    
        Returns
        -------
        list[dict]
            Each dictionary represents one row.
        """
        # Validate identifiers to avoid SQL injection.
        import re
    
        identifier_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    
        if not identifier_pattern.fullmatch(schema):
            raise ValueError(f"Invalid schema name: {schema}")
    
        if not identifier_pattern.fullmatch(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
    
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f'SELECT * FROM "{schema}"."{table_name}"'
                )
                rows = cur.fetchall()
                return DatabaseGetter.transform_data_to_list_of_dict(
                    rows, cur
                )


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
    def get_observations(station_id, fromm, time=None):
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
    
                base_query = f"""
                    SELECT *
                    FROM {Config.SILVER_SCHEMA}.{fromm}
                    WHERE station_id = %s
                """
                params = [station_id]
    
                if time is None:
                    pass
    
                elif isinstance(time, tuple):
                    if len(time) != 2:
                        logger.error(
                            "A time range must contain exactly two values"
                        )
                        raise ValueError(
                            "A time range must contain exactly two values"
                        )
    
                    start, end = time
    
                    if end < start:
                        logger.error("Invalid time range: end precedes start")
                        raise ValueError(
                            "The end of the time range must not precede the start"
                        )
    
                    base_query += """
                        AND time_step_fr > %s
                        AND time_step_fr < %s
                    """
                    params.extend([start, end])
    
                elif isinstance(time, date):
                    # datetime is a subclass of date, so handle it first.
                    # A datetime at midnight is treated as a specific timestep
                    # in this implementation, not as a date-only request.
                    if isinstance(time, datetime):
                        base_query += " AND time_step_fr = %s"
                        params.append(time)
    
                    else:
                        # Retrieve every observation for the given calendar day.
                        start = datetime.combine(time, datetime.min.time())
                        end = start + timedelta(days=1)
    
                        base_query += """
                            AND time_step_fr >= %s
                            AND time_step_fr < %s
                        """
                        params.extend([start, end])
    
                elif isinstance(time, str):
                    try:
                        if len(time) == 10:
                            # Date-only string: YYYY-MM-DD
                            day = date.fromisoformat(time)
                            start = datetime.combine(
                                day, datetime.min.time()
                            )
                            end = start + timedelta(days=1)
    
                            base_query += """
                                AND time_step_fr >= %s
                                AND time_step_fr < %s
                            """
                            params.extend([start, end])
    
                        else:
                            # Full datetime string: exact timestep
                            parsed_time = datetime.fromisoformat(time)
    
                            base_query += " AND time_step_fr = %s"
                            params.append(parsed_time)
    
                    except ValueError as exc:
                        logger.error("Invalid time format: %s", time)
                        raise ValueError(
                            "time must be a date (YYYY-MM-DD), a datetime "
                            "in ISO format, a date/datetime object, a tuple "
                            "of two bounds, or None"
                        ) from exc
    
                else:
                    logger.error("Unsupported time type: %s", type(time))
                    raise ValueError(
                        "time must be None, a date, a datetime, an ISO "
                        "string, or a tuple of two bounds"
                    )
    
                cur.execute(base_query, tuple(params))
                return cur.fetchall(), cur


    # @staticmethod
    # def get_observations(station_id, fromm, time = None):
    #     # if "6m" in fromm:
    #     #     dataclass_obj = ObservationInfrahoraire6mRecord
    #     # else:
    #     #     dataclass_obj = ObservationHoraireRecord

    #     with DatabaseConnection() as conn:
    #         with conn.cursor() as cur:
    #             if time is None:
    #                 cur.execute(f"""
    #                         SELECT * 
    #                         FROM {Config.SILVER_SCHEMA}.{fromm}
    #                         WHERE
    #                             station_id = %s 
    #                         """, (station_id,))
    #             else:
    #                 if isinstance(time, tuple):
    #                     if len(time) != 2:
    #                         logger.error("time if provided as a tuple it should contain two values")
    #                         raise ValueError
    #                     if time[1] < time[0]:
    #                         logger.error("Invalid time ranges")
    #                         raise ValueError
    #                     cur.execute(f"""
    #                             SELECT * 
    #                             FROM {Config.SILVER_SCHEMA}.{fromm}
    #                             WHERE
    #                                 station_id = %s and time_step_fr > %s and time_step_fr < %s
    #                             """, (station_id,time[0],time[1]))
    #                 elif isinstance(time, datetime) or isinstance(time, str):
    #                     cur.execute(f"""
    #                             SELECT * 
    #                             FROM {Config.SILVER_SCHEMA}.{fromm}
    #                             WHERE
    #                                 station_id = %s and time_step_fr = %s
                                
    #                             """, (station_id,time,))
    #                 else:
    #                     logger.error("In get_observations, the time should either be None to get all observations of the station, or a tuple to get a range of time, or datetime or iso string to get at specific timestep, other types are not handled")
    #                     raise ValueError
    #             return cur.fetchall(), cur


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
    def get_forecasts_for_day(station_id, fromm, day):
        """
        Retrieve the latest available forecast for every timestep
        within a specified calendar day.
    
        Args:
            station_id: Station identifier.
            fromm: Forecast table name.
            day: Requested day as a date, datetime, or ISO date string
                 (YYYY-MM-DD).
    
        Returns:
            A tuple containing the fetched rows and the database cursor.
        """
        if isinstance(day, datetime):
            day = day.date()
        elif isinstance(day, str):
            try:
                day = date.fromisoformat(day)
            except ValueError as exc:
                raise ValueError(
                    "day must be a date in YYYY-MM-DD format"
                ) from exc
        elif not isinstance(day, date):
            raise ValueError(
                "day must be a date, datetime, or YYYY-MM-DD string"
            )
    
        start_of_day = datetime.combine(day, time.min)
        start_of_next_day = start_of_day + timedelta(days=1)
    
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                        SELECT DISTINCT ON (station_id, time_step_fr) *
                        FROM {Config.SILVER_SCHEMA}.{fromm}
                        WHERE
                            station_id = %s
                            AND time_step_fr >= %s
                            AND time_step_fr < %s
                        ORDER BY
                            station_id,
                            time_step_fr,
                            run_time DESC;
                    """,
                    (station_id, start_of_day, start_of_next_day),
                )
    
                return cur.fetchall(), cur



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
    def get_stations():
        """Stations almost never change, so we keep them in memory for 1 hour."""
        if _STATIONS_CACHE["rows"] is not None and time.time() - _STATIONS_CACHE["ts"] < 3600:
            return _STATIONS_CACHE["rows"]
        rows = DatabaseGetter._load_stations()
        _STATIONS_CACHE.update(ts=time.time(), rows=rows)
        return rows

    @staticmethod
    def _load_stations() -> list[SilverObservationListeStationsRecords]:
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
    def get_model_run_times(fromm, days):
        time_before_specified_days = TimeManager.get_time_before(days)
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                        SELECT DISTINCT ON (run_time) run_time
                        FROM {Config.SILVER_SCHEMA}.{fromm}
                        where
                            run_time >= %s
                            """, (time_before_specified_days,))
                return cur.fetchall()


    @staticmethod
    def get_frontend_formatted_data_for_analysis(station, days):
        # Step 1 - get list of run_times based on the days requested
        per_run_analysis = []
        run_times = DatabaseGetter.get_model_run_times(Config.SILVER_FORECAST_AROME_TABLE_NAME, days)

        for run_time in run_times:
            # Step 1 - Get forecast data
            forecast_data = DatabaseGetter.get_forecast_run(station.station_id, Config.SILVER_FORECAST_AROME_TABLE_NAME, run_time)
            time_range = (forecast_data[0].time_step_fr, forecast_data[-1].time_step_fr)
            
            # Step 2 — fetch observations for the same time window
            observations_data, cur = DatabaseGetter.get_observations(
                station.station_id, Config.OBSERVATIONS_TABLE_NAME_HOURLY, time_range
            )
            analysis = analyser.analyse(
                DatabaseGetter.transform_list_of_objects_to_list_of_dict(forecast_data),
                DatabaseGetter.transform_data_to_list_of_dict(observations_data, cur)
            )

            per_run_analysis.append(analysis)
        aggregated_analysis = analyser.aggregate(per_run_analysis)
        return aggregated_analysis
        
    @staticmethod
    def get_previous_cumulative(
        station_id: str,
        run_time: datetime,
        current_time: datetime,
        variable_name: str
    ) -> float:
        """
        Fetches the cumulative global_radiation_j_m2 value of the timestep
        immediately before current_time for a given station and run.

        This is used as the baseline for de-accumulation so that the first
        entry in our forecast slice is correctly converted to instantaneous W/m².

        Returns 0.0 if no previous entry exists (i.e. current_time is the
        first timestep of the run).
        """
        sql = f"""
            SELECT {variable_name}
            FROM silver.forecast_arome
            WHERE station_id = %s
            AND run_time = %s
            AND time_step_fr < %s
            ORDER BY time_step_fr DESC
            LIMIT 1
        """
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (station_id, run_time, current_time))
                    row = cur.fetchone()
                    if row is None:
                        return 0.0
                    return float(row[0] or 0.0)
        except Exception as e:
            logger.error(f"Error fetching previous radiation: {e}")
            return 0.0

