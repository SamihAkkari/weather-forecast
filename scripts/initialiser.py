from src.config.config import Config
from src.data.db import DatabaseConnection


BRONZE_OBSERVATIONS_COLUMNS = """
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geo_id_insee TEXT,
    reference_time TEXT,
    insert_time TEXT,
    validity_time TEXT,
    t DOUBLE PRECISION,
    td DOUBLE PRECISION,
    tx DOUBLE PRECISION,
    tn DOUBLE PRECISION,
    u DOUBLE PRECISION,
    ux DOUBLE PRECISION,
    un DOUBLE PRECISION,
    dd DOUBLE PRECISION,
    ff DOUBLE PRECISION,
    dxy DOUBLE PRECISION,
    fxy DOUBLE PRECISION,
    dxi DOUBLE PRECISION,
    fxi DOUBLE PRECISION,
    rr1 DOUBLE PRECISION,
    t_10 DOUBLE PRECISION,
    t_20 DOUBLE PRECISION,
    t_50 DOUBLE PRECISION,
    t_100 DOUBLE PRECISION,
    vv DOUBLE PRECISION,
    etat_sol DOUBLE PRECISION,
    sss DOUBLE PRECISION,
    n DOUBLE PRECISION,
    insolh DOUBLE PRECISION,
    ray_glo01 DOUBLE PRECISION,
    pres DOUBLE PRECISION,
    pmer DOUBLE PRECISION
"""

SILVER_OBSERVATIONS_COLUMNS = """
    station_id TEXT,
    time_step_fr timestamptz,
    temperature_celsius DOUBLE PRECISION,
    humidity_percentage DOUBLE PRECISION,
    wind_direction_degree DOUBLE PRECISION,
    wind_speed_m_per_s DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    global_radiation_J_m2 DOUBLE PRECISION,
    transfer_time_fr timestamptz
"""

BRONZE_SP1_FORECAST_COLUMNS = """
    station_id BIGINT,
    run_time timestamptz,
    valid_time timestamptz,
    t2m DOUBLE PRECISION,
    r2 DOUBLE PRECISION,
    si10 DOUBLE PRECISION,
    wdir10 DOUBLE PRECISION,
    ssrd DOUBLE PRECISION,
    tp DOUBLE PRECISION,
    prmsl DOUBLE PRECISION,
    fg10 DOUBLE PRECISION,
    tsnowp DOUBLE PRECISION,
    ingestion_time timestamptz
"""

BRONZE_SP2_FORECAST_COLUMNS = """
    station_id BIGINT,
    run_time timestamptz,
    valid_time timestamptz,
    lcc DOUBLE PRECISION,
    mcc DOUBLE PRECISION,
    hcc DOUBLE PRECISION,
    CAPE_INS DOUBLE PRECISION,
    ingestion_time timestamptz
"""

SILVER_FORECAST_COLUMNS = """
    station_id TEXT,
    run_time timestamptz,
    time_step_fr timestamptz,
    forecast_step BIGINT,
    temperature_celsius DOUBLE PRECISION,
    humidity_percentage DOUBLE PRECISION,
    wind_direction_degree DOUBLE PRECISION,
    wind_speed_m_per_s DOUBLE PRECISION,
    CUMUL_precipitation_mm DOUBLE PRECISION,
    CUMUL_global_radiation_J_m2 DOUBLE PRECISION,
    total_cloud_cover DOUBLE PRECISION,
    cape_m2_s2 DOUBLE PRECISION,
    mean_sea_level_pressure DOUBLE PRECISION,
    CUMUL_snow_precipitation_mm DOUBLE PRECISION,
    wind_gust_m_per_s DOUBLE PRECISION,
    transfer_time_fr timestamptz,
    precipitation_mm DOUBLE PRECISION,
    global_radiation_J_m2 DOUBLE PRECISION,
    snow_precipitation_mm DOUBLE PRECISION
"""


def _execute(*statements: str) -> None:
    with DatabaseConnection() as conn, conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)


def _create_table(
    schema: str,
    table: str,
    columns_sql: str,
    hypertable_on: str | None = None,
) -> None:
    statements = [
        f"CREATE SCHEMA IF NOT EXISTS {schema}",
        f"CREATE TABLE IF NOT EXISTS {schema}.{table} ({columns_sql})",
    ]
    if hypertable_on:
        statements.insert(0, "CREATE EXTENSION IF NOT EXISTS timescaledb")
        statements.append(
            f"SELECT create_hypertable('{schema}.{table}', '{hypertable_on}', "
            "'station_id', 4, if_not_exists => TRUE)"
        )
    _execute(*statements)


def make_stations_table(CSV_FILE, SCHEMA, TABLE):
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
        station_id BIGINT,
        department_id BIGINT,
        name TEXT,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        altitude DOUBLE PRECISION,
        openning_date TEXT,
        pack TEXT
    );
    """

    with DatabaseConnection() as conn, conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        cur.execute(create_table_sql)
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{TABLE}")
        if cur.fetchone()[0] > 0:
            print(f"{SCHEMA}.{TABLE} already has data, skipping CSV load")
            return

        with open(CSV_FILE, "r") as csv_file:
            cur.copy_expert(
                f"COPY {SCHEMA}.{TABLE} FROM STDIN WITH CSV HEADER DELIMITER ';'",
                csv_file,
            )


def make_observations_horaire_table_without_data(SCHEMA, TABLE):
    _create_table(SCHEMA, TABLE, BRONZE_OBSERVATIONS_COLUMNS)


def make_silver_observation_horaire_table_without_data(SCHEMA, TABLE):
    _create_table(
        SCHEMA,
        TABLE,
        SILVER_OBSERVATIONS_COLUMNS,
        hypertable_on="time_step_fr",
    )


def make_bronze_sp1_arome_forecast_table_without_data(SCHEMA, TABLE):
    _create_table(SCHEMA, TABLE, BRONZE_SP1_FORECAST_COLUMNS)


def make_bronze_sp2_arome_forecast_table_without_data(SCHEMA, TABLE):
    _create_table(SCHEMA, TABLE, BRONZE_SP2_FORECAST_COLUMNS)


def make_silver_forecast_arome_table_without_data(SCHEMA, TABLE):
    _create_table(
        SCHEMA,
        TABLE,
        SILVER_FORECAST_COLUMNS,
        hypertable_on="run_time",
    )


def make_indexes_and_policies():
    """Create indexes and retention policy; safe to run on every start."""
    statements = [
        f"CREATE INDEX IF NOT EXISTS ix_b_sp1 ON {Config.BRONZE_SCHEMA}.{Config.BRONZE_SP1_FORECAST_TABLE_NAME} (run_time, valid_time)",
        f"CREATE INDEX IF NOT EXISTS ix_b_sp2 ON {Config.BRONZE_SCHEMA}.{Config.BRONZE_SP2_FORECAST_TABLE_NAME} (run_time, valid_time)",
        f"CREATE INDEX IF NOT EXISTS ix_b_obs ON {Config.BRONZE_SCHEMA}.{Config.OBSERVATIONS_TABLE_NAME_HOURLY} (validity_time)",
        f"CREATE INDEX IF NOT EXISTS ix_s_fc ON {Config.SILVER_SCHEMA}.{Config.SILVER_FORECAST_AROME_TABLE_NAME} (station_id, time_step_fr, run_time DESC)",
        f"SELECT add_retention_policy('{Config.SILVER_SCHEMA}.{Config.SILVER_FORECAST_AROME_TABLE_NAME}', INTERVAL '365 days', if_not_exists => true)",
    ]
    _execute(*statements)


if __name__ == "__main__":
    make_stations_table(
        "data/liste-stations-obs-metropole-om_completed.csv",
        Config.BRONZE_SCHEMA,
        Config.STATIONS_TABLE_NAME,
    )

    make_observations_horaire_table_without_data(
        Config.BRONZE_SCHEMA,
        Config.OBSERVATIONS_TABLE_NAME_HOURLY,
    )
    make_silver_observation_horaire_table_without_data(
        Config.SILVER_SCHEMA,
        Config.OBSERVATIONS_TABLE_NAME_HOURLY,
    )

    make_bronze_sp1_arome_forecast_table_without_data(
        Config.BRONZE_SCHEMA,
        Config.BRONZE_SP1_FORECAST_TABLE_NAME,
    )
    make_bronze_sp2_arome_forecast_table_without_data(
        Config.BRONZE_SCHEMA,
        Config.BRONZE_SP2_FORECAST_TABLE_NAME,
    )
    make_silver_forecast_arome_table_without_data(
        Config.SILVER_SCHEMA,
        Config.SILVER_FORECAST_AROME_TABLE_NAME,
    )
    make_indexes_and_policies()
