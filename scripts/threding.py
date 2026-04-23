import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ForecastAromeClient
from logging.handlers import RotatingFileHandler
from src.ingestion.ingestor import ForecastIngestor
from src.client.clients import ObservationsClient
from src.ingestion.ingestor import ObservationsIngestor
import logging
import threading
import glob


# delete old logs
for f in glob.glob("logs/app.log*"):
    os.remove(f)

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


obs_api = APIFactory.create("meteofrance_observations", "stations_horaire")
obs_client = ObservationsClient(obs_api)
obs_ingestor = ObservationsIngestor(obs_client)


description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1_available_data")
description_client = ForecastAromeClient(description_api)
fore_api_SP1= APIFactory.create("meteofrance_forecast_arome", "0025SP1")
fore_client_SP1 = ForecastAromeClient(fore_api_SP1)
fore_api_SP2= APIFactory.create("meteofrance_forecast_arome", "0025SP2")
fore_client_SP2 = ForecastAromeClient(fore_api_SP1)
fore_clients = [fore_client_SP1, fore_client_SP2]

fore_ingestor = ForecastIngestor(fore_clients, description_client)


t1 = threading.Thread(target=obs_ingestor.run_loop, name="ObservationsThread")
t2 = threading.Thread(target=fore_ingestor.run_loop, name="ForecastThread")

t1.start()
t2.start()

t1.join()
t2.join()
