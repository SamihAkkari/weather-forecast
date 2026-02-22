{{ config(
    materialized='table',
) }}

SELECT
    CASE 
        WHEN LENGTH(station_id::TEXT) < 8 THEN '0' || station_id::TEXT
        ELSE station_id::TEXT
    END AS station_id,
    department_id::TEXT AS department_id,
    LOWER(name) AS location_name,
    latitude,
    longitude,
    altitude,
    CASE
        WHEN openning_date ~ '^\d{2}/\d{2}/\d{4}$' THEN TO_DATE(openning_date, 'DD/MM/YYYY')
        WHEN openning_date ~ '^\d{4}-\d{2}-\d{2}$' THEN openning_date::DATE
        ELSE NULL
    END AS openning_date,
    LOWER(pack) AS station_type,
    DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris') AS transfer_time_fr
FROM {{ source('bronze', 'stations') }}