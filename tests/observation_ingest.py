
import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ObservationsClient
from src.ingestion.ingestor import ObservationsIngestor
from src.ingestion.time_manager import TimeManager
from src.processing.observations_processor import ObservationProcessor

import logging
from logging.handlers import RotatingFileHandler

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

api = APIFactory.create("meteofrance_observations", "stations_horaire")
client = ObservationsClient(api)

ingestor = ObservationsIngestor(client)
ingestor.run_once()


date = TimeManager.last_interval_iso(time_step = api.time_step_seconds, steps_back = api.steps_back)
params = {'date': date, 'format': 'json'}
response = client.fetch_data(params)

observation_processor = ObservationProcessor(response)
records = observation_processor.get_ready_to_ingest_records()

Ingestor = RealTimeIngestor(client)
Ingestor.run_loop()





params = {
    "referencetime": "2026-03-08T15:00:00Z",
    "time": "07H12H",
    "format": "grib2"
}
d = data_client.fetch_data(params = params)

description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1_available_data")
description_client = ForecastAromeClient(description_api)
d = description_client.fetch_data()

ingestor = ForecastIngestor(data_client, description_client)
ingestor.run_once()
