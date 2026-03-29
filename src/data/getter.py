
from src.config.config import Config
from src.data.db import DatabaseConnection
from src.data.models import ObservationListeStationsRecords, BaseRecord
import logging

logger = logging.getLogger(__name__)

class DatabaseGetter:
    
    @staticmethod
    def get_observations(station_id):
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                        SELECT * 
                        FROM {Config.SILVER_SCHEMA}.{Config.OBSERVATIONS_TABLE_NAME_6m}
                        WHERE
                            station_id = %s 
                        """, (station_id,))
                data = cur.fetchall()
                return data, cur

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
