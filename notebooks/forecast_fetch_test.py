# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 00:39:57 2026

@author: sakkari
"""

import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ForecastAromeClient
from src.processing.arome_forecast_processor import GribProcessor


data_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1")
data_client = ForecastAromeClient(data_api)

# description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1_available_data")
# description_client = ForecastAromeClient(description_api)


params = {
    "referencetime" : "2026-03-28T18:00:00Z",
    "time": ["00H06H", "49H51H"],
    "format": "grib2"
}

response = data_client.fetch_data(params = params)  # your API method

grib_processor = GribProcessor(response, params.get("referencetime"))
records = grib_processor.get_ready_to_ingest_records(data_client.api.record_class)