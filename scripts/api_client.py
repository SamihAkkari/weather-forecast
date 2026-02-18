import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
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

api = APIFactory.create("meteofrance_observations", "stations_infrahoraire-6m")
client = Client(api)
# response = client.request(params={'id_station': '77113002', 'format': 'json'})
response = client.request(params={'date': '2026-02-15T02:12:00Z', 'format':'json'})

data = response.json()

response.raise_for_status()
    
content_type = response.headers.get('Content-Type', '')