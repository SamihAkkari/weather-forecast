import psycopg2
import logging
from src.config.config import Config

logger = logging.getLogger(__name__)


class DatabaseConnection: 
    
    """Handles opening and closing DB connections."""
    def __init__(self):
        pass
    
    def __enter__(self):
        self.conn = psycopg2.connect(
            dbname=Config.POSTGRES_DB,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT
        )
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.conn.commit()   # success
        else:
            self.conn.rollback() # error
        self.conn.close()


class DatabaseRepository:
    
    # Observations table columns in order (for bulk inserts)

    OBSERVATIONS_COLUMNS = [
        'lat', 
        'lon', 
        'geo_id_insee', 
        'reference_time', 
        'insert_time', 
        'validity_time', 
        't', 
        'td',
        'u',
        'dd',
        'ff',
        'dxi10',
        'fxi10',
        'rr_per',
        't_10',
        't_20',
        't_50',
        't_100',
        'vv',
        'etat_sol',
        'sss',
        'insolh',
        'ray_glo01',
        'pres',
        'pmer'
    ]

    # Pre-built SQL for batch inserts
    OBSERVATIONS_INSERT_SQL = f"""
        INSERT INTO {Config.BRONZE_SCHEMA}.{Config.Data_TABLE_NAME} 
        ({', '.join(OBSERVATIONS_COLUMNS)}) 
        VALUES ({', '.join(['%s'] * len(OBSERVATIONS_COLUMNS))})
    """
    

    FORECAST_COLUMNS = [
    	'station_id',
      'run_time',
      'valid_time',
      't2m',
      'r2',
      'si10',
      'wdir10',
      'ssrd',
      'tp',
      'ingestion_time'
    ]

    FORECAST_INSERT_SQL = f"""
        INSERT INTO {Config.BRONZE_SCHEMA}.{Config.FORECAST_TABLE_NAME}
        ({', '.join(FORECAST_COLUMNS)})
        VALUES ({', '.join(['%s'] * len(FORECAST_COLUMNS))})
    """

    # FORECAST_RUN_SQL = """
    #     INSERT INTO forecast_runs (model, run_time, status, n_rows)
    #     VALUES (%s, %s, %s, %s)
    #     ON CONFLICT (model, run_time)
    #     DO UPDATE SET
    #         status     = EXCLUDED.status,
    #         n_rows     = EXCLUDED.n_rows,
    #         fetched_at = now()
    # """


    # # Stations table columns (for bulk inserts if needed)
    # STATIONS_COLUMNS = [
    #     'station_id',
    #     'department_id',
    #     'name',
    #     'latitude',
    #     'longitude',
    #     'altitude',
    #     'opening_date',
    #     'pack'
    # ]
    
    # STATIONS_INSERT_SQL = f"""
    #     INSERT INTO {Config.CORE_SCHEMA}.{Config.STATIONS_TABLE_NAME}
    #     ({', '.join(STATIONS_COLUMNS)})
    #     VALUES ({', '.join(['%s'] * len(STATIONS_COLUMNS))})
    # """

    @staticmethod
    def ingest(data):
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur = conn.cursor()
                    # Use the pre-built SQL statement
                    rows = [[row[col] for col in DatabaseRepository.OBSERVATIONS_COLUMNS] for row in data]
                    cur.executemany(DatabaseRepository.OBSERVATIONS_INSERT_SQL, rows)               
                    logger.info(f"Ingested {len(data)} observations")
        except Exception as e:
            logger.error(f"Error saving observation: {e}")
            raise


    @staticmethod
    def ingest_forecasts(data: list[dict]):
        """Mirrors your existing ingest() pattern exactly."""
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    rows = [
                        [row[col] for col in DatabaseRepository.FORECAST_COLUMNS]
                        for row in data
                    ]
                    cur.executemany(DatabaseRepository.FORECAST_INSERT_SQL, rows)
                    logger.info(f"Upserted {len(rows)} forecast rows")
        except Exception as e:
            logger.error(f"Error saving forecasts: {e}")
            raise


    @staticmethod
    def _ensure_schema_exists():
        """Create schema if it doesn't exist"""
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {Config.CORE_SCHEMA}")
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {Config.BRONZE_SCHEMA}")
                    logger.info(f"Schemas {Config.CORE_SCHEMA}, {Config.BRONZE_SCHEMA} ready")
        except Exception as e:
            logger.error(f"Error validating schemas: {e}")
            raise

    @staticmethod
    def _ensure_tables_exist():
        """Checks if bronze table exists"""
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                            SELECT to_regclass({Config.BRONZE_SCHEMA}.{Config.Data_TABLE_NAME})
                            """)
                table_exists = cur.fetchone()[0] is not None
                if not table_exists:
                    logger.error("Bronze table does not exist")
                else:
                    logger.info("Bronze tables is ready")
    
    def _this_date_is_already_ingested(date):
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                                SELECT 1 
                                FROM {Config.BRONZE_SCHEMA}.{Config.Data_TABLE_NAME}
                                WHERE validity_time = %s
                                LIMIT 1;
                                """, (date,))
                    exists = cur.fetchone() is not None
                    return exists
        except Exception as e:
            logger.error(f"Error checking if date {date} is already ingested: {e}")

    # @staticmethod
    # def is_run_already_ingested_forecast(model: str, run_time) -> bool:
    #     """Mirrors your _this_date_is_already_ingested() pattern."""
    #     try:
    #         with DatabaseConnection() as conn:
    #             with conn.cursor() as cur:
    #                 cur.execute("""
    #                     SELECT 1 FROM forecast_runs
    #                     WHERE model = %s
    #                     AND run_time = %s
    #                     AND status = 'success'
    #                     LIMIT 1
    #                 """, (model, run_time))
    #                 return cur.fetchone() is not None
    #     except Exception as e:
    #         logger.error(f"Error checking forecast run: {e}")
    #         raise


    @staticmethod
    def get_stations() -> list[dict]:
        """Fetch active stations — used by forecast extractor."""
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT station_id, latitude, longitude
                        FROM  {Config.BRONZE_SCHEMA}.{Config.STATIONS_TABLE_NAME}
                        ORDER BY station_id
                    """)
                    cols = [desc[0] for desc in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching stations: {e}")
            raise
    
    # @staticmethod
    # def mark_forecast_run(model: str, run_time, status: str, n_rows: int = 0):
    #     try:
    #         with DatabaseConnection() as conn:
    #             with conn.cursor() as cur:
    #                 cur.execute(
    #                     DatabaseRepository.FORECAST_RUN_SQL,
    #                     (model, run_time, status, n_rows)
    #                 )
    #     except Exception as e:
    #         logger.error(f"Error marking forecast run: {e}")
    #         raise