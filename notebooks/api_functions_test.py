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

from src.processing.viewer_service import get_viewer_data

from api.api import get_viewer_page_data
from api.api import get_analysis


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


get_viewer_page_data(lat, lng)

lat = 48.4638
lng = -3.6673

get_analysis(lat=lat, lng= lng)

