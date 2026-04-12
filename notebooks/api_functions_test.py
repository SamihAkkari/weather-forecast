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