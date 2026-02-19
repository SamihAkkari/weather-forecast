
SELECT 
	geo_id_insee as station_id, 
	validity_time::timestamptz AT TIME ZONE 'Europe/Paris' AS time_step_fr,
	t-273.15 as temperature_celcuis, 
	u as humidity_percentage, 
	dd as wind_direction_degree, 
	ff as wind_speed_m_per_s, 
	rr_per as precipitation_mm, 
	ray_glo01 as global_radiation_J_m2,
	DATE_TRUNC('minute', NOW() AT TIME ZONE 'Europe/Paris') AS transfer_time_fr
FROM bronze.observations
LIMIT 100