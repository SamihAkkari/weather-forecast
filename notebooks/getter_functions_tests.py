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

from src.ingestion.time_manager import TimeManager

station_id =  "01014002"
time = "2026-04-09 18:00:00+00"
time = TimeManager.utc_now_truncated(to="hour")
time = TimeManager.utc_to_france(time)
time = TimeManager.convert_to_iso(time)

fromm = Config.FORECAST_TABLE_NAME
fromm = Config.OBSERVATIONS_TABLE_NAME_HOURLY

data = DatabaseGetter.get_formatted_observations(station_id, fromm, time)

data = DatabaseGetter.get_forecasts(station_id, fromm, time = time, exactly_at_time = False)

data = DatabaseGetter.get_formatted_forecasts(station_id, fromm, time = time, exactly_at_time = False)

data = DatabaseGetter.get_frontend_formatted_data_for_basicV(station_id, time = time)



stations= DatabaseGetter.get_stations()

stations = DatabaseGetter.get_stations_to_show_on_map_in_basicV()