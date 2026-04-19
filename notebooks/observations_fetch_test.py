# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 14:32:07 2026

@author: sakkari
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 00:39:57 2026

@author: sakkari
"""

import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ObservationsClient
from src.ingestion.ingestor import ObservationsIngestor
from src.ingestion.time_manager import TimeManager
from src.processing.observations_processor import ObservationProcessor

import logging
from logging.handlers import RotatingFileHandler


api = APIFactory.create("meteofrance_observations", "stations_infrahoraire-6m")
client = ObservationsClient(api)

date = TimeManager.last_interval_iso(360, 3)

params = {
    "date": date,
    "format": "json"
}

response = client.fetch_data(params = params)  # your API method

grib_processor = GribProcessor(response, params.get("referencetime"))
records = grib_processor.get_ready_to_ingest_records(data_client.api.record_class)