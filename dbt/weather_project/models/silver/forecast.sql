{{ config(materialized='incremental') }}

-- 1. This returns only the last run time availbale in silver forecast
WITH last_silver AS (
    SELECT COALESCE(MAX(run_time), '1900-01-01'::timestamp) AS last_time
    FROM {{ this }}
),

-- 2. This returns the data in bronze that do not exist in silver (using the last run time from previous query)
base AS (
    SELECT
        station_id::TEXT AS station_id,
        run_time::timestamptz AT TIME ZONE 'Europe/Paris' AS run_time,
        valid_time::timestamptz AT TIME ZONE 'Europe/Paris' AS time_step_fr,
        t2m AS temperature_celsius,
        r2 AS humidity_percentage,
        wdir10 AS wind_direction_degree,
        si10 AS wind_speed_m_per_s,
        tp AS precipitation_mm,
        ssrd AS global_radiation_J_m2
    FROM {{ source('bronze', 'forecast') }}
    WHERE run_time IS NOT NULL
      AND run_time::timestamptz AT TIME ZONE 'Europe/Paris'
          > (SELECT last_time FROM last_silver)
),

-- 3. This returns all the stations from bronze stations table
stations AS (
    SELECT DISTINCT station_id::TEXT AS station_id
    FROM {{ source('bronze', 'stations') }}
),

-- 4. ALL (station, run_time) pairs, then it will be used to select the data from base in the last select
station_time AS (
    SELECT DISTINCT
        s.station_id,
        b.run_time
    FROM stations s
    CROSS JOIN (SELECT DISTINCT run_time FROM base) b
)

-- 5. main query that fetches the data into silver
SELECT
    CASE 
        WHEN LENGTH(st.station_id::TEXT) < 8 THEN '0' || st.station_id::TEXT
        ELSE st.station_id::TEXT
    END AS station_id,
    st.run_time,
    b.time_step_fr,
    b.temperature_celsius,
    b.humidity_percentage,
    b.wind_direction_degree,
    b.wind_speed_m_per_s,
    b.precipitation_mm,
    b.global_radiation_J_m2,
    DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris') AS transfer_time_fr
FROM station_time st
LEFT JOIN base b
    ON st.station_id = b.station_id
   AND st.run_time = b.run_time