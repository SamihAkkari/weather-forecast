

-- Table making 
create table silver.observations (
	station_id TEXT,
	time_step_fr timestamptz,
	temperature_celsius Double precision, 
	humidity_percentage Double precision, 
	wind_direction_degree Double precision, 
	wind_speed_m_per_s Double precision, 
	precipitation_mm Double precision, 
	global_radiation_J_m2 Double precision,
	transfer_time_fr timestamptz
)


-- Table insertion

-- Returns a table with the dates that do not exist on silver but do exist in bronze 
WITH last_silver AS (
    SELECT COALESCE(MAX(time_step_fr), '1900-01-01'::timestamp) AS last_time
    FROM silver.observations
),

-- Returns a table with only the new timestamps that do not exist in silver (one column table)
new_times AS (
    SELECT DISTINCT
        validity_time::timestamptz AT TIME ZONE 'Europe/Paris' AS time_step_fr
    FROM bronze.observations b
    CROSS JOIN last_silver l
    WHERE validity_time::timestamptz AT TIME ZONE 'Europe/Paris' > l.last_time
),

-- Returns all the stations from silver.stations keeping only the station_id column
all_stations AS (
    SELECT station_id::TEXT
    FROM silver.stations 
),

-- Returns a full grid table containing all the stations and new timestamps (stations × new timesteps)
-- for example if silver is two timesteps behind, this table will list all the station ids and 
-- assign for each station a timestep resulting in duplicating the station id in 2rows
-- so if stations are 2147 and i have two new timesteps then the full size of teh table is
-- 2147*2
grid AS (
    SELECT
        s.station_id,
        t.time_step_fr
    FROM all_stations s
    CROSS JOIN new_times t
),

-- Returns a cleaned table of the new timesteps from silver (at this point the missing stations are not yet replaced by null)
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
    FROM bronze.observations b
    CROSS JOIN last_silver l
    WHERE validity_time::timestamptz AT TIME ZONE 'Europe/Paris' > l.last_time
)

-- FINAL INSERT INTO SILVER
INSERT INTO silver.observations (
    station_id,
    time_step_fr,
    temperature_celsius,
    humidity_percentage,
    wind_direction_degree,
    wind_speed_m_per_s,
    precipitation_mm,
    global_radiation_J_m2,
    transfer_time_fr
)

-- Returns the table that contains all the new timesteps in addition to setting null to missing stations
-- This is done via the left join with the grid table that contains all the stations (grid being the base table in the left join)
SELECT
    g.station_id,
    g.time_step_fr,
    c.temperature_celsius,
    c.humidity_percentage,
    c.wind_direction_degree,
    c.wind_speed_m_per_s,
    c.precipitation_mm,
    c.global_radiation_J_m2,
    DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris')
FROM grid g
LEFT JOIN clean_obs c
    ON g.station_id = c.station_id
   AND g.time_step_fr = c.time_step_fr;

