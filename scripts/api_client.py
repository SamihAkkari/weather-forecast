import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.client import Client
import logging
from logging.handlers import RotatingFileHandler
import cfgrib


import numpy as np
import pandas as pd

import xarray as xr

def group_datasets(datasets: list[xr.Dataset]) -> dict[str, xr.Dataset]:
    """
    Load AROME GRIB2 file into logically grouped datasets.
    Industry practice: split by physical meaning, not by cfgrib internals.
    """    
    grouped = {
        'surface_instant': [],
        'surface_accum': [],
        '2m': [],
        '10m': [],
        'pressure_levels': [],
        'other': []
    }
    
    for ds in datasets:
        vars_ = set(ds.data_vars)
        
        if any(v in vars_ for v in ['u10', 'v10', 'fg10', 'efg10']):
            grouped['10m'].append(ds)
        elif any(v in vars_ for v in ['t2m', 'r2', 'd2m']):
            grouped['2m'].append(ds)
        elif any(v in vars_ for v in ['tp', 'ssrd', 'tsnowp']):
            grouped['surface_accum'].append(ds)
        elif 'isobaricInhPa' in ds.coords:
            grouped['pressure_levels'].append(ds)
        else:
            grouped['surface_instant'].append(ds)
    
    # Merge within each group
    result = {}
    for group, ds_list in grouped.items():
        if ds_list:
            try:
                result[group] = xr.merge(ds_list)
            except Exception:
                # If merge fails, keep as list — don't force incompatible data
                result[group] = ds_list
    
    return result


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
api = APIFactory.create("meteofrance_forecast_arome", "0025SP1")

client = Client(api)
# response = client.request(params={'id_station': '77113002', 'format': 'json'})

params = {
    "referencetime": "2026-03-05T15:00:00Z",
    "time": "07H12H",
    "format": "grib2"
}

response = client.request(params=params)
response.raise_for_status()

open("file.grib2", "wb").write(response.content)

data = response.json()
content_type = response.headers.get('Content-Type', '')

datasets = cfgrib.open_datasets("file.grib2")
data = group_datasets(datasets)





