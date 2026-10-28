# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 23:09:06 2026

@author: sakkari
"""

import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.config.config import Config
from src.data.getter import DatabaseGetter
import pandas as pd
import numpy as np
from src.processing import analysis_processor
from src.processing.spatial import find_nearest_station


lat = 49.0190
lng = 3.2533

stations = DatabaseGetter.get_stations()
nearest  = find_nearest_station(stations, lat, lng)
station_id = nearest.station_id
# logger.info(f"Analysis for station {station_id}")


analysis_processor.compute_analysis(days= 7, station_id = None, 
                                    forecast_table = Config.SILVER_SCHEMA+"."+Config.SILVER_FORECAST_AROME_TABLE_NAME, 
                                    obs_table= Config.SILVER_SCHEMA+"."+Config.OBSERVATIONS_TABLE_NAME_HOURLY)




# data_forecast = DatabaseGetter.get_full_table(schema = Config.SILVER_SCHEMA, table_name = Config.SILVER_FORECAST_AROME_TABLE_NAME)
# forecast_table = pd.DataFrame(data_forecast)

# data_observation = DatabaseGetter.get_full_table(schema = Config.SILVER_SCHEMA, table_name = Config.OBSERVATIONS_TABLE_NAME_HOURLY)
# obs_table = pd.DataFrame(data_observation)

# variable = "temperature_celsius"
# run_time = "2026-10-23T17:00:00+00:00"

# variable_forecast = forecast_table[forecast_table['run_time'] == run_time][["station_id", "time_step_fr", variable]]
# variable_forecast.sort_values(["station_id", "time_step_fr"])
# first_time_step = variable_forecast ['time_step_fr'].min()
# last_time_step = variable_forecast ['time_step_fr'].max()
# variable_forecast["step"] = (variable_forecast.groupby("station_id").cumcount() + 1)

# variable_observation = obs_table[["station_id", "time_step_fr", variable]]

# df_merged = pd.merge(
#     variable_forecast,
#     variable_observation,
#     on=["station_id", "time_step_fr"],
#     how="left",
#     suffixes=("_forecast", "_observed"),
#     validate="many_to_one",
# )

# df_merged = df_merged.dropna()[['temperature_celsius_forecast', 'temperature_celsius_observed', 'step']]

# step_8 = df_merged[df_merged['step'] == 10]
# np.mean(abs(step_8["temperature_celsius_forecast"] - step_8["temperature_celsius_observed"]))







 