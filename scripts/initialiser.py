
import pandas as pd
import psycopg2
import os
from src.config.config import Config


def make_stations_table(CSV_FILE, SCHEMA, TABLE):
    # Modify CREATE TABLE to include schema
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
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

    # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()

    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute(create_table_sql)

    # ---- Step 5: load CSV using COPY
    with open(CSV_FILE, "r") as f:
        cur.copy_expert(
            f"COPY {SCHEMA}.{TABLE} FROM STDIN WITH CSV HEADER DELIMITER ';'",
            f
        )

    conn.commit()
    cur.close()
    conn.close()


def make_observations_horaire_table_without_data(SCHEMA, TABLE):
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
    make_observations_table = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
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
    );
    """
        # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()
    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute(make_observations_table)

    conn.commit()
    cur.close()
    conn.close()

def make_observations_infrahoraire6m_table_without_data(SCHEMA, TABLE):
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
    make_observations_table = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
        lat DOUBLE PRECISION,
        lon DOUBLE PRECISION,
        geo_id_insee TEXT,
        reference_time TEXT, 
        insert_time TEXT, 
        validity_time TEXT,
        t DOUBLE PRECISION,
        td DOUBLE PRECISION,
        u DOUBLE PRECISION,
        dd DOUBLE PRECISION,
        ff DOUBLE PRECISION,
        dxi10 DOUBLE PRECISION,
        fxi10 DOUBLE PRECISION,
        rr_per DOUBLE PRECISION,
        t_10 DOUBLE PRECISION,
        t_20 DOUBLE PRECISION,
        t_50 DOUBLE PRECISION,
        t_100 DOUBLE PRECISION,
        vv DOUBLE PRECISION,
        etat_sol DOUBLE PRECISION,
        sss DOUBLE PRECISION,
        insolh DOUBLE PRECISION,
        ray_glo01 DOUBLE PRECISION,
        pres DOUBLE PRECISION,
        pmer DOUBLE PRECISION
    );
    """

        # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()
    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute(make_observations_table)

    conn.commit()
    cur.close()
    conn.close()


def make_silver_observation_infrahoraire6m_table_without_data(SCHEMA, TABLE):
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
    make_observations_table = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
    	station_id TEXT,
        time_step_fr timestamptz,
        temperature_celsius Double precision, 
        humidity_percentage Double precision, 
        wind_direction_degree Double precision, 
        wind_speed_m_per_s Double precision, 
        precipitation_mm Double precision, 
        global_radiation_J_m2 Double precision,
        transfer_time_fr timestamptz
    );
    """


    #Convert to Timescale hypertable
    create_hypertable_sql = f"""
    SELECT create_hypertable(
        '{SCHEMA}.{TABLE}',
        'time_step_fr',
        'station_id',
        4,
        if_not_exists => TRUE
    );
    """

        # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute(make_observations_table)

    # THIS makes it TimescaleDB
    cur.execute(create_hypertable_sql)

    conn.commit()
    cur.close()
    conn.close()

def make_silver_observation_horaire_table_without_data(SCHEMA, TABLE):
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
    make_observations_table = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
    	station_id TEXT,
        time_step_fr timestamptz,
        temperature_celsius Double precision, 
        humidity_percentage Double precision, 
        wind_direction_degree Double precision, 
        wind_speed_m_per_s Double precision, 
        precipitation_mm Double precision, 
        global_radiation_J_m2 Double precision,
        transfer_time_fr timestamptz
    );
    """

    #Convert to Timescale hypertable
    create_hypertable_sql = f"""
    SELECT create_hypertable(
        '{SCHEMA}.{TABLE}',
        'time_step_fr',
        'station_id',
        4,
        if_not_exists => TRUE
    );
    """

        # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute(make_observations_table)

    # THIS makes it TimescaleDB
    cur.execute(create_hypertable_sql)

    conn.commit()
    cur.close()
    conn.close()


def make_bronze_sp1_arome_forecast_table_without_data(SCHEMA, TABLE):
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
    make_forecast_table = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
        station_id BIGINT,
        run_time   timestamptz,
        valid_time timestamptz,
        t2m Double precision,
        r2 Double precision,
        si10 Double precision,
        wdir10 Double precision,
        ssrd Double precision,
        tp Double precision,
        prmsl Double precision,
        fg10 Double precision,
        tsnowp Double precision,
        ingestion_time timestamptz
    );
    """

        # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()
    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute( make_forecast_table)

    conn.commit()
    cur.close()
    conn.close()

def make_bronze_sp2_arome_forecast_table_without_data(SCHEMA, TABLE):
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
    make_forecast_table = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
        station_id BIGINT,
        run_time   timestamptz,
        valid_time timestamptz,
        lcc Double precision,
        mcc Double precision,
        hcc Double precision,
        CAPE_INS Double precision,
        ingestion_time timestamptz
    );
    """

        # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()
    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute( make_forecast_table)

    conn.commit()
    cur.close()
    conn.close()


def make_silver_forecast_arome_table_without_data(SCHEMA, TABLE):
    make_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"
    make_observations_table = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
    	station_id TEXT,
        run_time timestamptz,
        time_step_fr timestamptz,
        temperature_celsius Double precision, 
        humidity_percentage Double precision, 
        wind_direction_degree Double precision, 
        wind_speed_m_per_s Double precision, 
        precipitation_mm Double precision, 
        global_radiation_J_m2 Double precision,
        total_cloud_cover Double precision,
        cape_m2_s2 Double precision,
        mean_sea_level_pressure Double precision,
        snow_precipitation_mm Double precision,
        wind_gust_m_per_s Double precision,
        transfer_time_fr timestamptz
    );
    """

    #Convert to Timescale hypertable
    create_hypertable_sql = f"""
    SELECT create_hypertable(
        '{SCHEMA}.{TABLE}',
        'run_time',
        'station_id',
        4,
        if_not_exists => TRUE
    );
    """

        # ---- Step 2: connect to Postgres
    conn = psycopg2.connect(
        dbname = Config.POSTGRES_DB,
        user = Config.POSTGRES_USER,
        password = Config.POSTGRES_PASSWORD,
        host = "localhost",
        port = Config.POSTGRES_PORT
    )

    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # ---- Step 3: create schema if not exists
    cur.execute(make_schema_sql)

    # ---- Step 4: create table inside schema
    cur.execute(make_observations_table)

    # THIS makes it TimescaleDB
    cur.execute(create_hypertable_sql)

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    make_stations_table("data/liste-stations-obs-metropole-om_completed.csv", 
                        Config.BRONZE_SCHEMA, 
                        Config.STATIONS_TABLE_NAME)
    
    make_observations_horaire_table_without_data(Config.BRONZE_SCHEMA, Config.OBSERVATIONS_TABLE_NAME_HOURLY)
    make_silver_observation_horaire_table_without_data(Config.SILVER_SCHEMA, Config.OBSERVATIONS_TABLE_NAME_HOURLY)

    make_observations_infrahoraire6m_table_without_data(Config.BRONZE_SCHEMA, Config.OBSERVATIONS_TABLE_NAME_6m)
    make_silver_observation_infrahoraire6m_table_without_data(Config.SILVER_SCHEMA, Config.OBSERVATIONS_TABLE_NAME_6m)
    
    make_bronze_sp1_arome_forecast_table_without_data(Config.BRONZE_SCHEMA, Config.BRONZE_SP1_FORECAST_TABLE_NAME)
    make_bronze_sp2_arome_forecast_table_without_data(Config.BRONZE_SCHEMA, Config.BRONZE_SP2_FORECAST_TABLE_NAME)
    make_silver_forecast_arome_table_without_data(Config.SILVER_SCHEMA, Config.SILVER_FORECAST_AROME_TABLE_NAME)
 