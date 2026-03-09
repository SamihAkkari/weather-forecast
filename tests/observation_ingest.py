
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

api = APIFactory.create("meteofrance_observations", "stations_infrahoraire-6m")
client = ObservationsClient(api)

ingestor = ObservationsIngestor(client)
ingestor.run_once()