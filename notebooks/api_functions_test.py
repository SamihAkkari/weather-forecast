# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 14:09:07 2026

@author: sakkari
"""

from fastapi import FastAPI
from src.data.getter import DatabaseGetter
from src.ingestion.time_manager import TimeManager
from fastapi.middleware.cors import CORSMiddleware
from src.processing import spatial
from src.processing.spatial import find_nearest_station
from src.config.config import Config
from src.processing.pv_processor import compute_pv_production
from src.processing import utils

lat = 48.8647
lng = 2.3236

system_capacity_kw = 3.0
inverter_capacity_kw = 2.5
tilt = 30
azimuth = 180
losses_pct = 14.0
inverter_efficiency = 0.96

stations = DatabaseGetter.get_stations()
nearest = find_nearest_station(stations, lat, lng)

current_time = TimeManager.current_france_time_iso(time_truncation="hour")

forecast_raw, cur = DatabaseGetter.get_forecasts_at_time_step(
    station_id=nearest.station_id,
    fromm=Config.SILVER_FORECAST_AROME_TABLE_NAME,
    time=current_time,
    exactly_at_time=False,
)
forecast = DatabaseGetter.transform_data_to_list_of_dict(forecast_raw, cur)
forecast = utils.unaccumulate(forecast, "global_radiation_j_m2", nearest.station_id)

# # Get the run_time of this forecast so we can find the previous entry
# # run_time comes from the first forecast entry
# run_time = forecast[0].get("run_time")

# # Fetch the cumulative radiation value just before our slice starts
# # so the first entry in our slice is correctly de-accumulated
# previous_cumulative = DatabaseGetter.get_previous_cumulative(
#     station_id=nearest.station_id,
#     run_time=run_time,
#     current_time=forecast[0].get("time_step_fr"),
#     variable_name = "global_radiation_j_m2"
# )

altitude = float(nearest.altitude or 0)

result = compute_pv_production(
    forecast=forecast,
    lat=lat,
    lng=lng,
    altitude=altitude,
    system_capacity_kw=system_capacity_kw,
    inverter_capacity_kw  = inverter_capacity_kw ,
    tilt=tilt,
    azimuth=azimuth,
    losses_pct=losses_pct,
    inverter_efficiency = inverter_efficiency
)














def get_frontend_formatted_data_for_basicV(location: dict):
    # Get current time 
    time = TimeManager.current_france_time_iso(time_truncation="hour")
    
    # Get longitude and latitude of selected location
    ...

    # Get elevatino of the selected location
    ...

    # Get nearest station of the selected location
    stations = DatabaseGetter.get_stations()
    nearest_station = spatial.find_nearest_station(stations, location["lat"], location["lng"])

    # Get data for the nearest station and the current time    
    data = DatabaseGetter.get_frontend_formatted_data_for_basicV(nearest_station, time = time)
    return data


location = {
    "lat" : 48,
    "lng" : 3
    }


# Get nearest station of the selected location
stations = DatabaseGetter.get_stations()
nearest_station = spatial.find_nearest_station(stations, location["lat"], location["lng"])