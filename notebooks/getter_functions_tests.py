# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 00:27:59 2026

@author: sakkari
"""

import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.config.config import Config
from src.data.db import DatabaseConnection
from src.data.getter import DatabaseGetter
from src.processing import spatial
from src.ingestion.time_manager import TimeManager
from src.processing.spatial import find_nearest_station

from src.processing.viewer_service import get_viewer_data

stations = DatabaseGetter.get_stations()

lat = 48.8215
lng = 2.3378
nearest_station = find_nearest_station(stations, lat, lng)

current_time = TimeManager.current_france_time_iso(time_truncation="hour")

raw_data = DatabaseGetter.get_frontend_formatted_data_for_basicV(
        station=nearest_station,
        time=current_time
    )

D = get_viewer_data(lat, lng)


station_id =  "01014002"
time = "2026-04-09 18:00:00+00"
time = TimeManager.utc_now_truncated(to="hour")
time = TimeManager.utc_to_france(time)
time = TimeManager.convert_to_iso(time)

fromm = Config.SILVER_FORECAST_AROME_TABLE_NAME
# fromm = Config.OBSERVATIONS_TABLE_NAME_HOURLY

data = DatabaseGetter.get_formatted_observations(station_id, fromm, time)

data = DatabaseGetter.get_forecasts(station_id, fromm, time = time, exactly_at_time = False)

data = DatabaseGetter.get_formatted_forecasts(station_id, fromm, time = time, exactly_at_time = False)

data = DatabaseGetter.get_frontend_formatted_data_for_basicV(station_id, time = time)

DatabaseGetter.get_observations(station_id, fromm, time = time)


stations= DatabaseGetter.get_stations()

stations = DatabaseGetter.get_stations_to_show_on_map_in_basicV()


run_time = '2026-04-22 20:00:00+00'
data = DatabaseGetter.get_forecast_run("01014002", Config.SILVER_FORECAST_AROME_TABLE_NAME, run_time)



# Step 1 - Get forecast data
forecast_data = DatabaseGetter.get_forecast_run("01014002", Config.SILVER_FORECAST_AROME_TABLE_NAME, run_time)
time_range = (forecast_data[0].time_step_fr, forecast_data[-1].time_step_fr)

# Step 2 — fetch observations for the same time window
observations_data, cur = DatabaseGetter.get_observations(
    "01014002", Config.OBSERVATIONS_TABLE_NAME_HOURLY, time_range
)

from src.processing import analysis_processor as analysis
analysis.compute_analysis(
    DatabaseGetter.transform_list_of_objects_to_list_of_dict(forecast_data),
    DatabaseGetter.transform_data_to_list_of_dict(observations_data, cur),
    "123"
    )



data, cur = DatabaseGetter.get_model_run_times(Config.SILVER_FORECAST_AROME_TABLE_NAME, 5)


# Step 1 - Get nearest station of the selected location
stations = DatabaseGetter.get_stations()
nearest_station = spatial.find_nearest_station(stations, 45, 2)

DatabaseGetter.get_frontend_formatted_data_for_analysis(nearest_station , days=5)


