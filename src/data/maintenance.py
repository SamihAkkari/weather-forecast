import logging
import random
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import Config
from src.data.db import DatabaseConnection

logger = logging.getLogger(__name__)
PARIS = ZoneInfo("Europe/Paris")

BRONZE = Config.BRONZE_SCHEMA
SILVER = Config.SILVER_SCHEMA
BRONZE_FORECAST_TABLES = [Config.BRONZE_SP1_FORECAST_TABLE_NAME, Config.BRONZE_SP2_FORECAST_TABLE_NAME]
SILVER_FORECAST = Config.SILVER_FORECAST_AROME_TABLE_NAME


def _vacuum(tables: list[tuple[str, str]], full: bool = False) -> None:
    """tables = [(schema, table), ...]. VACUUM cannot run inside a transaction."""
    options = "FULL, ANALYZE" if full else "ANALYZE"
    with DatabaseConnection() as conn:
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                for schema, table in tables:
                    cur.execute(f'VACUUM ({options}) "{schema}"."{table}"')
                    logger.info("%s.%s: VACUUM (%s) done", schema, table, options)
        finally:
            conn.autocommit = False      # the connection goes back to the pool

def thin_forecast_runs(dry_run: bool = False, lookback_days: int = 30, full_vacuum: bool = False) -> None:
    """
    For every COMPLETED day (Paris date < today), keep ONE random forecast run and
    delete the other runs of that day from silver AND bronze.
    The latest run overall (the one shown on the front) is never touched: a day that
    contains it is skipped and handled on a later night.
    """
    today = datetime.now(PARIS).date()
    tables_to_compact = [SILVER_FORECAST] + BRONZE_FORECAST_TABLES

    with DatabaseConnection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT max(run_time) FROM {SILVER}.{SILVER_FORECAST}")
            latest = cur.fetchone()[0]
            if latest is None:
                logger.info("No forecast runs in silver, nothing to thin")
                return

            cur.execute(
                f"""SELECT DISTINCT run_time FROM {SILVER}.{SILVER_FORECAST}
                    WHERE run_time >= now() - make_interval(days => %s)
                    ORDER BY run_time""",
                (lookback_days,),
            )
            runs = [r[0] for r in cur.fetchall()]

            by_day = defaultdict(list)
            for rt in runs:
                by_day[rt.astimezone(PARIS).date()].append(rt)

            for day, day_runs in sorted(by_day.items()):
                if day >= today:
                    continue                      # today is still in progress
                if latest in day_runs:
                    continue                      # protect the run displayed on the front
                if len(day_runs) <= 1:
                    continue                      # already thinned

                keep = random.choice(day_runs)
                to_delete = [r for r in day_runs if r != keep]
                logger.info("Day %s: keeping run %s, deleting %d runs: %s",
                            day, keep, len(to_delete), to_delete)
                if dry_run:
                    continue

                cur.execute(
                    f"DELETE FROM {SILVER}.{SILVER_FORECAST} WHERE run_time = ANY(%s::timestamptz[])",
                    (to_delete,),
                )
                logger.info("  silver: %d rows deleted", cur.rowcount)
                for table in BRONZE_FORECAST_TABLES:
                    cur.execute(
                        f"DELETE FROM {BRONZE}.{table} WHERE run_time = ANY(%s::timestamptz[])",
                        (to_delete,),
                    )
                    logger.info("  bronze.%s: %d rows deleted", table, cur.rowcount)

    # Deletions are committed when the first DatabaseConnection closes.
    _vacuum([(SILVER, SILVER_FORECAST), 
             (BRONZE, Config.BRONZE_SP1_FORECAST_TABLE_NAME),
             (BRONZE, Config.BRONZE_SP2_FORECAST_TABLE_NAME)], full = full_vacuum)


def purge_old_bronze(keep_days: int = 3, full_vacuum:bool = False) -> None:
    """Delete bronze rows older than keep_days. Silver is NOT touched."""
    with DatabaseConnection() as conn:
        with conn.cursor() as cur:
            for table in BRONZE_FORECAST_TABLES:
                cur.execute(
                    f"DELETE FROM {BRONZE}.{table} WHERE run_time < now() - make_interval(days => %s)",
                    (keep_days,),
                )
                logger.info("bronze.%s: %d old rows deleted", table, cur.rowcount)
            cur.execute(
                f"""DELETE FROM {BRONZE}.{Config.OBSERVATIONS_TABLE_NAME_HOURLY}
                    WHERE validity_time::timestamptz < now() - make_interval(days => %s)""",
                (keep_days,),
            )
            logger.info("bronze.observations_hourly: %d old rows deleted", cur.rowcount)
    
    # Second: physically compact the tables.
    _vacuum([(BRONZE, Config.OBSERVATIONS_TABLE_NAME_HOURLY), 
             (BRONZE, Config.BRONZE_SP1_FORECAST_TABLE_NAME),
             (BRONZE, Config.BRONZE_SP2_FORECAST_TABLE_NAME)], full = full_vacuum)
