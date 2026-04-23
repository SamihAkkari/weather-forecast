{{ config(
    materialized='incremental',
    tags=['forecast_arome']
) }}

WITH 
-- 1. Combine both bronze tables on keys and filter for new data
base AS (
    SELECT 
        COALESCE(b1.station_id, b2.station_id) as station_id,
        COALESCE(b1.run_time, b2.run_time) as run_time,
        COALESCE(b1.valid_time, b2.valid_time) as valid_time,
        b1.t2m, b1.r2, b1.wdir10, b1.si10, b1.tp, b1.ssrd,
        b2.lcc, b2.mcc, b2.hcc, b2.CAPE_INS,
        ROW_NUMBER() OVER (
            PARTITION BY COALESCE(b1.station_id, b2.station_id), COALESCE(b1.run_time, b2.run_time), COALESCE(b1.valid_time, b2.valid_time)
            ORDER BY GREATEST(b1.ingestion_time, b2.ingestion_time) DESC
        ) AS rn
    FROM bronze.forecast_sp1_arome b1
    INNER JOIN bronze.forecast_sp2_arome b2 
        ON b1.station_id = b2.station_id 
        AND b1.run_time = b2.run_time 
        AND b1.valid_time = b2.valid_time
    WHERE b1.run_time IS NOT NULL
    
    {% if is_incremental() %}
    -- Only look at records that don't exist in Silver yet
    AND NOT EXISTS (
        SELECT 1
        FROM {{ this }} s
        WHERE s.station_id = LPAD(b1.station_id::TEXT, 8, '0')
          AND s.run_time = b1.run_time::timestamptz AT TIME ZONE 'Europe/Paris'
          AND s.time_step_fr = b1.valid_time::timestamptz AT TIME ZONE 'Europe/Paris'
    )
    {% endif %}
),

-- 2. Clean base to keep only the latest ingestion
deduped_base AS (
    SELECT * FROM base WHERE rn = 1
),

-- 3. Logic for stations that should have had data but were missing in Bronze
missing AS (
    SELECT
        s.station_id,
        tg.run_time,
        tg.valid_time
    FROM (SELECT DISTINCT station_id FROM bronze.stations) s
    CROSS JOIN (SELECT DISTINCT run_time, valid_time FROM deduped_base) tg
    WHERE NOT EXISTS (
        SELECT 1
        FROM deduped_base b
        WHERE b.station_id::TEXT = s.station_id::TEXT
          AND b.run_time = tg.run_time
          AND b.valid_time = tg.valid_time
    )
),

final_union AS (
    SELECT
        station_id, run_time, valid_time,
        t2m, r2, wdir10, si10, tp, ssrd, lcc, mcc, hcc, CAPE_INS 
    FROM deduped_base
    UNION ALL
    SELECT
        station_id, run_time, valid_time,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
    FROM missing
)

SELECT
    LPAD(station_id::TEXT, 8, '0') AS station_id,
    run_time::timestamptz AT TIME ZONE 'Europe/Paris'       AS run_time,
    valid_time::timestamptz AT TIME ZONE 'Europe/Paris'     AS time_step_fr,
    t2m - 273.15  AS temperature_celsius,
    r2   AS humidity_percentage,
    wdir10 AS wind_direction_degree,
    si10   AS wind_speed_m_per_s,
    tp     AS precipitation_mm,
    ssrd   AS global_radiation_J_m2,
    1 - (1 - lcc) * (1 - mcc) * (1 - hcc) AS total_cloud_cover,
    CAPE_INS as cape_m2_s2,
    DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris') AS transfer_time_fr
FROM final_union