{{ config(
    materialized='incremental',
    tags=['observations_6m']
) }}

WITH last_silver AS (
    SELECT COALESCE(MAX(time_step_fr), '1900-01-01'::timestamp) AS last_time
    FROM {{ this }}
),

new_times AS (
    SELECT DISTINCT
        validity_time::timestamptz AT TIME ZONE 'Europe/Paris' AS time_step_fr
    FROM {{ source('bronze', 'observations_6m') }} b
    CROSS JOIN last_silver l
    WHERE validity_time::timestamptz AT TIME ZONE 'Europe/Paris' > l.last_time
),

all_stations AS (
    SELECT station_id::TEXT
    FROM {{ ref('stations') }}
),

grid AS (
    SELECT
        s.station_id,
        t.time_step_fr
    FROM all_stations s
    CROSS JOIN new_times t
),

clean_obs AS (
    SELECT
        geo_id_insee::TEXT AS station_id,
        validity_time::timestamptz AT TIME ZONE 'Europe/Paris' AS time_step_fr,
        t - 273.15 AS temperature_celsius,
        u AS humidity_percentage,
        dd AS wind_direction_degree,
        ff AS wind_speed_m_per_s,
        rr_per AS precipitation_mm,
        ray_glo01 AS global_radiation_J_m2
    FROM {{ source('bronze', 'observations_6m') }} b
    CROSS JOIN last_silver l
    WHERE validity_time::timestamptz AT TIME ZONE 'Europe/Paris' > l.last_time
)

SELECT
    g.station_id,
    g.time_step_fr,
    c.temperature_celsius,
    c.humidity_percentage,
    c.wind_direction_degree,
    c.wind_speed_m_per_s,
    c.precipitation_mm,
    c.global_radiation_J_m2,
    DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris') AS transfer_time_fr
FROM grid g
LEFT JOIN clean_obs c
    ON g.station_id = c.station_id
   AND g.time_step_fr = c.time_step_fr