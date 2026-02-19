
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


def make_observations_table_without_data(SCHEMA, TABLE):
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

if __name__ == "__main__":
    make_stations_table("data/liste-stations-obs-metropole-om_completed.csv", 
                        Config.BRONZE_SCHEMA, 
                        Config.STATIONS_TABLE_NAME)
    make_observations_table_without_data(Config.BRONZE_SCHEMA, Config.Data_TABLE_NAME)