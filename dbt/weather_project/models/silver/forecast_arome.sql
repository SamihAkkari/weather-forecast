{{ config(
    materialized='incremental',
    tags=['forecast_arome']
) }}

-- Full forecast history, used only to calculate previous values.
-- This CTE must not have the incremental NOT EXISTS filter.
WITH 
-- 1. Combine both bronze tables on keys and filter for new data
base AS (
    SELECT 
        COALESCE(b1.station_id, b2.station_id) as station_id,
        COALESCE(b1.run_time, b2.run_time) as run_time,
        COALESCE(b1.valid_time, b2.valid_time) as valid_time,

        NULLIF(b1.t2m, 'NaN'::double precision) AS t2m,
        NULLIF(b1.r2, 'NaN'::double precision) AS r2,
        NULLIF(b1.wdir10, 'NaN'::double precision) AS wdir10,
        NULLIF(b1.si10, 'NaN'::double precision) AS si10,
        NULLIF(b1.tp, 'NaN'::double precision) AS tp,
        NULLIF(b1.ssrd, 'NaN'::double precision) AS ssrd,
        NULLIF(b2.lcc, 'NaN'::double precision) AS lcc,
        NULLIF(b2.mcc, 'NaN'::double precision) AS mcc,
        NULLIF(b2.hcc, 'NaN'::double precision) AS hcc,
        NULLIF(b2.CAPE_INS, 'NaN'::double precision) AS CAPE_INS,
        NULLIF(b1.prmsl, 'NaN'::double precision) AS prmsl,
        NULLIF(b1.fg10, 'NaN'::double precision) AS fg10,
        NULLIF(b1.tsnowp, 'NaN'::double precision) AS tsnowp,

        ROW_NUMBER() OVER (
            PARTITION BY b1.station_id, b1.run_time
            ORDER BY b1.valid_time
        ) AS forecast_step,

        LAG(b1.tp) OVER (
            PARTITION BY b1.station_id, b1.run_time
            ORDER BY b1.valid_time
        ) AS previous_tp,

        LAG(b1.ssrd) OVER (
            PARTITION BY b1.station_id, b1.run_time
            ORDER BY b1.valid_time
        ) AS previous_ssrd,

        LAG(b1.tsnowp) OVER (
            PARTITION BY b1.station_id, b1.run_time
            ORDER BY b1.valid_time
        ) AS previous_tsnowp,

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
)

-- 3. Logic for stations that should have had data but were missing in Bronze
-- missing AS (
--     SELECT
--         s.station_id,
--         tg.run_time,
--         tg.valid_time
--     FROM (SELECT DISTINCT station_id FROM bronze.stations) s
--     CROSS JOIN (SELECT DISTINCT run_time, valid_time FROM deduped_base) tg
--     WHERE NOT EXISTS (
--         SELECT 1
--         FROM deduped_base b
--         WHERE b.station_id::TEXT = s.station_id::TEXT
--           AND b.run_time = tg.run_time
--           AND b.valid_time = tg.valid_time
--     )
-- ),

-- final_union AS (
--     SELECT
--         station_id, run_time, valid_time,
--         t2m, r2, wdir10, si10, tp, ssrd, lcc, mcc, hcc, CAPE_INS, prmsl, fg10, tsnowp
--     FROM deduped_base
--     UNION ALL
--     SELECT
--         station_id, run_time, valid_time,
--         NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
--     FROM missing
-- ),

-- cleaned AS (
--     SELECT
--         station_id,
--         run_time,
--         valid_time,

--         NULLIF(t2m, 'NaN'::double precision) AS t2m,
--         NULLIF(r2, 'NaN'::double precision) AS r2,
--         NULLIF(wdir10, 'NaN'::double precision) AS wdir10,
--         NULLIF(si10, 'NaN'::double precision) AS si10,
--         NULLIF(tp, 'NaN'::double precision) AS tp,
--         NULLIF(ssrd, 'NaN'::double precision) AS ssrd,
--         NULLIF(lcc, 'NaN'::double precision) AS lcc,
--         NULLIF(mcc, 'NaN'::double precision) AS mcc,
--         NULLIF(hcc, 'NaN'::double precision) AS hcc,
--         NULLIF(CAPE_INS, 'NaN'::double precision) AS CAPE_INS,
--         NULLIF(prmsl, 'NaN'::double precision) AS prmsl,
--         NULLIF(fg10, 'NaN'::double precision) AS fg10,
--         NULLIF(tsnowp, 'NaN'::double precision) AS tsnowp

--     FROM final_union
-- )

SELECT
    LPAD(station_id::TEXT, 8, '0') AS station_id,
    run_time::timestamptz AT TIME ZONE 'Europe/Paris'       AS run_time,
    valid_time::timestamptz AT TIME ZONE 'Europe/Paris'     AS time_step_fr,
    forecast_step, 
    t2m - 273.15  AS temperature_celsius,
    r2   AS humidity_percentage,
    wdir10 AS wind_direction_degree,
    si10   AS wind_speed_m_per_s,
    tp     AS CUMUL_precipitation_mm,
    ssrd   AS CUMUL_global_radiation_J_m2,
    ROUND((100 - ((100 - ROUND(lcc::numeric, 2)) *(100 - ROUND(mcc::numeric, 2)) *(100 - ROUND(hcc::numeric, 2))) / 10000.0)::numeric, 2) AS total_cloud_cover,
    CAPE_INS as cape_m2_s2,
    prmsl AS mean_sea_level_pressure,
    fg10 AS wind_gust_m_per_s,
    tsnowp AS CUMUL_snow_precipitation_mm,
    DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris') AS transfer_time_fr,
	CASE
    WHEN forecast_step = 2 THEN tp -- because first step forecast is alway null
    WHEN tp IS NULL OR previous_tp IS NULL THEN NULL
    ELSE tp - previous_tp
	END AS precipitation_mm,
	
	CASE
	    WHEN forecast_step = 2 THEN ssrd
	    WHEN ssrd IS NULL OR previous_ssrd IS NULL THEN NULL
	    ELSE ssrd - previous_ssrd
	END AS global_radiation_J_m2,
	
	CASE
	    WHEN forecast_step = 2 THEN tsnowp
	    WHEN tsnowp IS NULL OR previous_tsnowp IS NULL THEN NULL
	    ELSE tsnowp - previous_tsnowp
	END AS snow_precipitation_mm    
FROM deduped_base