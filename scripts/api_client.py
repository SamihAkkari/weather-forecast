import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api import MeteoFranceAPI
from src.client.client import Client
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
)
api = MeteoFranceAPI(selected_endpoint_name='observations')
client = Client(api)
response = client.request(params={'id_station': '77113002', 'format': 'json'})