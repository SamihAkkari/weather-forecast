-- Check the rows in silver but not in bronze
select * 
from silver.observations_6m s
where not exists (
select 1
from bronze.observations_6m b
where s.station_id = b.geo_id_insee
and s.time_step_fr = b.validity_time::timestamptz AT TIME ZONE 'Europe/Paris'
)

-- Check the rows in bronze but not in silver
select * 
from bronze.observations_6m s
where not exists (
select 1
from silver.observations_6m b
where s.station_id = b.geo_id_insee
and s.time_step_fr = b.validity_time::timestamptz AT TIME ZONE 'Europe/Paris'
)

-- Get the number of duplicated rows in a table
SELECT SUM(cnt - 1) AS rows_dropped
FROM (
    SELECT COUNT(*) AS cnt
    FROM silver.observations_6m
    GROUP BY station_id, time_step_fr
    HAVING COUNT(*) > 1
) t;