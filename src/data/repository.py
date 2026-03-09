
import logging
from src.config.config import Config
from src.data.models import ObservationListeStationsRecords, BaseRecord
from src.data.db import DatabaseConnection

logger = logging.getLogger(__name__)





class DatabaseRepository:

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
    def _build_insert_sql(model_cls, table: str, conflict_columns: list[str] = None) -> str:
        cols        = model_cls.columns()
        placeholders = ', '.join(['%s'] * len(cols))
        col_names    = ', '.join(cols)

        sql = f"""
            INSERT INTO {table} ({col_names})
            VALUES ({placeholders})
        """

        # if conflict_columns:
        #     updates = ', '.join(
        #         f"{c} = EXCLUDED.{c}"
        #         for c in cols
        #         if c not in conflict_columns
        #     )
        #     conflict = ', '.join(conflict_columns)
        #     sql += f"ON CONFLICT ({conflict}) DO UPDATE SET {updates}"

        return sql
    
    @staticmethod
    def _insert(
        records        : list,
        table          : str,
        conflict_cols  : list[str] | None = None
    ):
        if not records:
            logger.warning(f"No records to insert into {table}")
            return

        sql = DatabaseRepository._build_insert_sql(
            type(records[0]),
            table=table,
            conflict_columns=conflict_cols
        )

        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.executemany(sql, [r.values() for r in records])
                    logger.info(f"Inserted {len(records)} rows into {table}")
        except Exception as e:
            logger.error(f"Error inserting into {table}: {e}")
            raise

    @staticmethod
    def insert_observations(records: list[BaseRecord], target_table_name: str):
        DatabaseRepository._insert(
            records,
            table=f"{Config.BRONZE_SCHEMA}.{target_table_name}"
        )

    @staticmethod
    def insert_forecasts(records: list[BaseRecord], target_table_name: str):
        DatabaseRepository._insert(
            records,
            table=f"{Config.BRONZE_SCHEMA}.{target_table_name}"
        )


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

    # @staticmethod
    # def _ensure_tables_exist():
    #     """Checks if bronze table exists"""
    #     with DatabaseConnection() as conn:
    #         with conn.cursor() as cur:
    #             cur.execute(f"""
    #                         SELECT to_regclass({Config.BRONZE_SCHEMA}.{Config.Data_TABLE_NAME})
    #                         """)
    #             table_exists = cur.fetchone()[0] is not None
    #             if not table_exists:
    #                 logger.error("Bronze table does not exist")
    #             else:
    #                 logger.info("Bronze tables is ready")
    
    def _this_date_is_already_ingested(date, target_table_name: str):
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                                SELECT 1 
                                FROM {Config.BRONZE_SCHEMA}.{target_table_name}
                                WHERE validity_time = %s
                                LIMIT 1;
                                """, (date,))
                    exists = cur.fetchone() is not None
                    return exists
        except Exception as e:
            logger.error(f"Error checking if date {date} is already ingested: {e}")

    @staticmethod
    def forecast_run_already_ingested(reference_time, target_table_name: str):
        """Mirrors your _this_date_is_already_ingested() pattern."""
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT 1 
                        FROM {Config.BRONZE_SCHEMA}.{target_table_name}
                        WHERE run_time = %s
                        LIMIT 1
                    """, (reference_time,))
                    return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking forecast run: {e}")
            raise


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



    # @staticmethod
    # def get_stations() -> list[dict]:
    #     """Fetch active stations — used by forecast extractor."""
    #     try:
    #         with DatabaseConnection() as conn:
    #             with conn.cursor() as cur:
    #                 cur.execute(f"""
    #                     SELECT station_id, latitude, longitude
    #                     FROM  {Config.BRONZE_SCHEMA}.{Config.STATIONS_TABLE_NAME}
    #                     ORDER BY station_id
    #                 """)
    #                 cols = [desc[0] for desc in cur.description]
    #                 return [dict(zip(cols, row)) for row in cur.fetchall()]
    #     except Exception as e:
    #         logger.error(f"Error fetching stations: {e}")
    #         raise
    
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