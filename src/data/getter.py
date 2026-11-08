import logging
import time as T
from datetime import date, datetime, time, timedelta
from typing import Tuple, List

from src.config.config import Config
from src.data.db import DatabaseConnection
from src.data.models import SilverObservationListeStationsRecords
logger = logging.getLogger(__name__)

_STATIONS_CACHE = {"ts": 0.0, "rows": None}

class DatabaseGetter:


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
        if _STATIONS_CACHE["rows"] is not None and T.time() - _STATIONS_CACHE["ts"] < 3600:
            return _STATIONS_CACHE["rows"]
        rows = DatabaseGetter._load_stations()
        _STATIONS_CACHE.update(ts=T.time(), rows=rows)
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
