{{ config(
    materialized='incremental',
    tags=['forecast_arome']
) }}

WITH pending_runs AS (
    SELECT DISTINCT b1.run_time
    FROM bronze.forecast_sp1_arome b1
    WHERE b1.run_time IS NOT NULL
    {% if is_incremental() %}
      AND NOT EXISTS (
        SELECT 1 FROM {{ this }} s
        WHERE s.station_id   = LPAD(b1.station_id::TEXT, 8, '0')
          AND s.run_time     = b1.run_time
          AND s.time_step_fr = b1.valid_time
      )
    {% endif %}
),

-- 1. Join SP1 and SP2: a row exists only if BOTH have it
joined AS (
    SELECT
        b1.station_id, b1.run_time, b1.valid_time,
        NULLIF(b1.t2m,    'NaN'::double precision) AS t2m,
        NULLIF(b1.r2,     'NaN'::double precision) AS r2,
        NULLIF(b1.wdir10, 'NaN'::double precision) AS wdir10,
        NULLIF(b1.si10,   'NaN'::double precision) AS si10,
        NULLIF(b1.tp,     'NaN'::double precision) AS tp,
        NULLIF(b1.ssrd,   'NaN'::double precision) AS ssrd,
        NULLIF(b1.prmsl,  'NaN'::double precision) AS prmsl,
        NULLIF(b1.fg10,   'NaN'::double precision) AS fg10,
        NULLIF(b1.tsnowp, 'NaN'::double precision) AS tsnowp,
        NULLIF(b2.lcc,      'NaN'::double precision) AS lcc,
        NULLIF(b2.mcc,      'NaN'::double precision) AS mcc,
        NULLIF(b2.hcc,      'NaN'::double precision) AS hcc,
        NULLIF(b2.CAPE_INS, 'NaN'::double precision) AS CAPE_INS,
        GREATEST(b1.ingestion_time, b2.ingestion_time) AS ingestion_time
    FROM bronze.forecast_sp1_arome b1
    INNER JOIN bronze.forecast_sp2_arome b2
        ON  b1.station_id = b2.station_id
        AND b1.run_time   = b2.run_time
        AND b1.valid_time = b2.valid_time
    WHERE b1.run_time IN (SELECT run_time FROM pending_runs)
),

-- 2. Deduplicate FIRST (keep the latest ingestion)
deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY station_id, run_time, valid_time
            ORDER BY ingestion_time DESC
        ) AS rn
    FROM joined
),

-- 3. Windows over the FULL run (no silver filter here)
base AS (
    SELECT *,
        ROW_NUMBER() OVER w AS forecast_step,
        LAG(tp)     OVER w AS previous_tp,
        LAG(ssrd)   OVER w AS previous_ssrd,
        LAG(tsnowp) OVER w AS previous_tsnowp
    FROM deduped
    WHERE rn = 1
    WINDOW w AS (PARTITION BY station_id, run_time ORDER BY valid_time)
)

-- 4. Only now keep rows that are not yet in silver
SELECT
    LPAD(station_id::TEXT, 8, '0') AS station_id,
    run_time   AS run_time,
    valid_time AS time_step_fr,
    forecast_step,
    t2m - 273.15 AS temperature_celsius,
    r2           AS humidity_percentage,
    wdir10       AS wind_direction_degree,
    si10         AS wind_speed_m_per_s,
    tp           AS CUMUL_precipitation_mm,
    ssrd         AS CUMUL_global_radiation_J_m2,
    ROUND((100 - ((100 - ROUND(lcc::numeric, 2)) * (100 - ROUND(mcc::numeric, 2)) * (100 - ROUND(hcc::numeric, 2))) / 10000.0)::numeric, 2) AS total_cloud_cover,
    CAPE_INS     AS cape_m2_s2,
    prmsl        AS mean_sea_level_pressure,
    fg10         AS wind_gust_m_per_s,
    tsnowp       AS CUMUL_snow_precipitation_mm,
    DATE_TRUNC('minute', NOW()) AS transfer_time_fr,
    CASE
        WHEN forecast_step = 2 THEN tp
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
FROM base
{% if is_incremental() %}
WHERE NOT EXISTS (
    SELECT 1 FROM {{ this }} s
    WHERE s.station_id   = LPAD(base.station_id::TEXT, 8, '0')
      AND s.run_time     = base.run_time
      AND s.time_step_fr = base.valid_time
)
{% endif %}