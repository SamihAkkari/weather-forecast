import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ForecastAromeClient
import xarray as xr
import cfgrib

import logging
from logging.handlers import RotatingFileHandler
from src.processing.arome_forecast_processor import GribProcessor
# from src.processing.grib_grouping_rules import AROME_GROUPING_RULES
from src.data.repository import DatabaseRepository
from src.ingestion.time_manager import TimeManager
from src.ingestion.ingestor import ForecastIngestor


handler = RotatingFileHandler(
    "logs/app.log",
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        handler,
    ],
    force = True
)

data_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1")
data_client = ForecastAromeClient(data_api)

description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1_available_data")
description_client = ForecastAromeClient(description_api)

ingestor = ForecastIngestor(data_client, description_client)
ingestor.run_once()
ingestor.run_loop()

data_api= APIFactory.create("meteofrance_forecast_arome", "0025SP2")
data_client = ForecastAromeClient(data_api)


description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP2_available_data")
description_client = ForecastAromeClient(description_api)

ingestor = ForecastIngestor(data_client, description_client)
ingestor.run_once()
ingestor.run_loop()