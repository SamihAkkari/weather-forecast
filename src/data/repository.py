
import logging
from src.config import Config
from src.data.models import BaseRecord
from src.data.db import DatabaseConnection
import re
from datetime import datetime, timedelta, timezone
logger = logging.getLogger(__name__)

class DatabaseRepository:

    @staticmethod
    def _build_insert_sql(model_cls, table: str) -> str:
        cols        = model_cls.columns()
        placeholders = ', '.join(['%s'] * len(cols))
        col_names    = ', '.join(cols)

        sql = f"""
            INSERT INTO {table} ({col_names})
            VALUES ({placeholders})
        """

        return sql
    
    @staticmethod
    def _insert(
        records        : list,
        table          : str
    ):
        if not records:
            logger.warning(f"No records to insert into {table}")
            return

        sql = DatabaseRepository._build_insert_sql(
            type(records[0]),
            table=table
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
            raise
    @staticmethod
    def forecast_interval_already_ingested(
        forecast_interval: str,
        target_table_name: str,
        reference_time: str,
    ) -> bool:
        """Return True if data for this forecast interval is already ingested."""
    
        # Parse the interval, e.g. "00H06H" -> hours 0 to 6
        match = re.fullmatch(r"(\d{2})H(\d{2})H", forecast_interval)
        if not match:
            raise ValueError(f"Invalid forecast interval: {forecast_interval}")
    
        start_hour, end_hour = map(int, match.groups())
    
        if start_hour > end_hour:
            raise ValueError(f"Invalid forecast interval: {forecast_interval}")
    
        # Parse ISO 8601 reference time, including the trailing Z
        run_time = datetime.fromisoformat(reference_time.replace("Z", "+00:00"))
    
        if run_time.tzinfo is None:
            run_time = run_time.replace(tzinfo=timezone.utc)
    
        start_time = run_time + timedelta(hours=start_hour)
        end_time = run_time + timedelta(hours=end_hour)
    
        # Validate table name before interpolating it into SQL
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target_table_name):
            raise ValueError(f"Invalid table name: {target_table_name}")
    
        query = f"""
            SELECT 1
            FROM {Config.BRONZE_SCHEMA}.{target_table_name}
            WHERE run_time = %s
              AND valid_time >= %s
              AND valid_time <= %s
            LIMIT 1
        """
    
        try:
            with DatabaseConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        query,
                        (run_time, start_time, end_time),
                    )
                    return cur.fetchone() is not None
    
        except Exception:
            logger.exception(
                "Error checking ingestion for run %s, interval %s, table %s",
                reference_time,
                forecast_interval,
                target_table_name,
            )
            raise