{{ config(
    materialized='incremental',
    tags=['forecast_arome']
) }}

WITH 
-- OBJECTIVE:
--	1. Select the data rows that exist in bronze but not in silver
--	2. If a certain row is duplicated in bronze it selects only the one ingected at the end
base_SP1 AS (
    SELECT *
    FROM (
        SELECT
            b.station_id,
            b.run_time,
            b.valid_time,
            b.t2m,
            b.r2,
            b.wdir10,
            b.si10,
            b.tp,
            b.ssrd,
            ROW_NUMBER() OVER (
                PARTITION BY b.station_id, b.run_time, b.valid_time
                ORDER BY ingestion_time DESC
            ) AS rn
        FROM bronze.forecast_sp1_arome b
        WHERE b.run_time IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM silver.forecast_arome s
            WHERE s.station_id::INT = b.station_id
              AND s.run_time = b.run_time::timestamptz AT TIME ZONE 'Europe/Paris'
              AND s.time_step_fr = b.valid_time::timestamptz AT TIME ZONE 'Europe/Paris'
        )
    ) t
    WHERE t.rn = 1
),

-- OBJECTIVE:
-- 	1. Contructs a time grid table of run_time/valid_time 
--	2. Only consider run_time/valid_time combos that actually appear in base
relevant_time_grids_SP1 AS (
    SELECT DISTINCT run_time, valid_time
    FROM base_SP1
),

-- OBJECTIVE:
-- 	1. Contructs a time grid table of station_id/run_time/valid_time if a certain station is missing from bronze
missing_SP1 AS (
    SELECT
        s.station_id,
        tg.run_time,
        tg.valid_time
    FROM (
        SELECT DISTINCT station_id FROM bronze.stations  -- or your source macro
    ) s
    JOIN relevant_time_grids_SP1 tg ON TRUE
    -- Only keep station+combo pairs missing from bronze entirely
    WHERE NOT EXISTS (
        SELECT 1
        FROM bronze.forecast_sp1_arome b
        WHERE b.station_id::TEXT = s.station_id::TEXT
          AND b.run_time = tg.run_time
          AND b.valid_time = tg.valid_time
    )
),

final_SP1 AS (
    SELECT
        station_id, 
		run_time, 
		valid_time,
        t2m,
        r2,
        wdir10,
        si10,
        tp,
        ssrd   
    FROM base
    UNION ALL
    SELECT
        station_id, run_time, valid_time,
        NULL, NULL, NULL, NULL, NULL, NULL
    FROM missing_SP1
),


base_SP2 AS (
    SELECT *
    FROM (
        SELECT
            b.station_id,
            b.run_time,
            b.valid_time,
            b.t2m,
            b.r2,
            b.wdir10,
            b.si10,
            b.tp,
            b.ssrd,
            ROW_NUMBER() OVER (
                PARTITION BY b.station_id, b.run_time, b.valid_time
                ORDER BY ingestion_time DESC
            ) AS rn
        FROM bronze.forecast_sp2_arome b
        WHERE b.run_time IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM silver.forecast_arome s
            WHERE s.station_id::INT = b.station_id
              AND s.run_time = b.run_time::timestamptz AT TIME ZONE 'Europe/Paris'
              AND s.time_step_fr = b.valid_time::timestamptz AT TIME ZONE 'Europe/Paris'
        )
    ) t
    WHERE t.rn = 1
),

-- OBJECTIVE:
-- 	1. Contructs a time grid table of run_time/valid_time 
--	2. Only consider run_time/valid_time combos that actually appear in base
relevant_time_grids_SP2 AS (
    SELECT DISTINCT run_time, valid_time
    FROM base_SP2
),

-- OBJECTIVE:
-- 	1. Contructs a time grid table of station_id/run_time/valid_time if a certain station is missing from bronze
missing_SP2 AS (
    SELECT
        s.station_id,
        tg.run_time,
        tg.valid_time
    FROM (
        SELECT DISTINCT station_id FROM bronze.stations  -- or your source macro
    ) s
    JOIN relevant_time_grids_SP2 tg ON TRUE
    -- Only keep station+combo pairs missing from bronze entirely
    WHERE NOT EXISTS (
        SELECT 1
        FROM bronze.forecast_sp2_arome b
        WHERE b.station_id::TEXT = s.station_id::TEXT
          AND b.run_time = tg.run_time
          AND b.valid_time = tg.valid_time
    )
),

final_SP2 AS (
    SELECT
        station_id, 
		run_time, 
		valid_time,
        t2m,
        r2,
        wdir10,
        si10,
        tp,
        ssrd   
    FROM base
    UNION ALL
    SELECT
        station_id, run_time, valid_time,
        NULL, NULL, NULL, NULL, NULL, NULL
    FROM missing_SP2
),











SELECT
    CASE 
        WHEN LENGTH(station_id::TEXT) < 8 THEN '0' || station_id::TEXT
        ELSE station_id::TEXT
    END AS station_id,
    run_time::timestamptz AT TIME ZONE 'Europe/Paris'       AS run_time,
    valid_time::timestamptz AT TIME ZONE 'Europe/Paris'     AS time_step_fr,
	t2m - 273.15  AS temperature_celsius,
 	r2   AS humidity_percentage,
	wdir10 AS wind_direction_degree,
	si10   AS wind_speed_m_per_s,
	tp     AS precipitation_mm,
	ssrd   AS global_radiation_J_m2,
    DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris') AS transfer_time_fr
FROM final