
import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.client import Client
from src.ingestion.ingestor import RealTimeIngestor

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
client = Client(api)
Ingestor = RealTimeIngestor(client)
Ingestor.run_loop()





import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.client import Client
import xarray as xr
import cfgrib

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

api= APIFactory.create("meteofrance_forecast_arome", "0025SP1")
client = Client(api)

params = {
    "referencetime": "2026-03-05T15:00:00Z",
    "time": "07H12H",
    "format": "grib2"
}

## 2. get_active_stations()
from src.data.repository import DatabaseRepository
stations = DatabaseRepository.get_stations()

## 3. download_grib(url, tmp_path)
api = APIFactory.create("meteofrance_forecast_arome", "0025SP1")
client = Client(api)
params = {
    "referencetime": "2026-03-05T15:00:00Z",
    "time": "07H12H",
    "format": "grib2"
}
response = client.request(params=params)
response.raise_for_status()
open("file.grib2", "wb").write(response.content)


## 4. open_and_group_datasets(tmp_path)
datasets = cfgrib.open_datasets("file.grib2")
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
data = group_datasets(datasets)

## extract_at_stations(grouped_datasets, stations)
import numpy as np
import pandas as pd

def _extract_at_stations(forecast, stations, run_time) -> list[dict]:
    """
    Vectorized extraction — finds all station grid indices at once.
    2140 stations: ~30s → <1s
    """

    # --- 1. Build station arrays once ---
    station_ids = np.array([s['station_id'] for s in stations])
    lats        = np.array([s['latitude']   for s in stations])
    lons        = np.array([s['longitude']  for s in stations])

    # --- 2. Get grid coordinates once ---
    grid_lats = forecast['10m']['wdir10'].latitude.values   # shape: (n_lat,)
    grid_lons = forecast['10m']['wdir10'].longitude.values  # shape: (n_lon,)

    # --- 3. Find nearest grid index for ALL stations at once ---
    # shape: (n_stations,) — one index per station
    lat_idxs = np.abs(grid_lats[:, None] - lats[None, :]).argmin(axis=0)
    lon_idxs = np.abs(grid_lons[:, None] - lons[None, :]).argmin(axis=0)

    # --- 4. Extract all variables for all stations in one shot ---
    def get_all_stations(group, var):
        """
        Returns array of shape (n_stations, n_steps) or None.
        One operation instead of 2140 individual .sel() calls.
        """
        try:
            da = forecast[group][var].values  # shape: (n_steps, n_lat, n_lon)
            return da[:, lat_idxs, lon_idxs].T  # shape: (n_stations, n_steps)
        except (KeyError, AttributeError, TypeError):
            return None

    wdir10 = get_all_stations('10m',           'wdir10')
    si10   = get_all_stations('10m',           'si10')
    t2m    = get_all_stations('2m',            't2m')
    r2     = get_all_stations('2m',            'r2')
    tp     = get_all_stations('surface_accum', 'tp')
    ssrd   = get_all_stations('surface_accum', 'ssrd')

    valid_times    = forecast['10m']['valid_time'].values
    n_stations     = len(stations)
    n_steps        = len(valid_times)
    run_time_ts    = pd.Timestamp(run_time)
    valid_times_ts = [pd.Timestamp(vt) for vt in valid_times]

    # --- 5. Build records ---
    records = []
    for s_idx in range(n_stations):
        for t_idx in range(n_steps):

            def val(arr, transform=None):
                if arr is None:
                    return None
                v = float(arr[s_idx, t_idx])
                return transform(v) if transform else v

            records.append({
                'station_id'     : int(station_ids[s_idx]),
                'run_time'       : run_time_ts,
                'valid_time'     : valid_times_ts[t_idx],
                't2m'            : val(t2m),
                'r2'             : val(r2),
                'si10'           : val(si10),
                'wdir10'         : val(wdir10),
                'tp'             : val(tp),
                'ssrd'           : val(ssrd),
                'ingestion_time' : pd.Timestamp('now', tz='UTC'),
            })

    return records

run_time = params["referencetime"]
records = _extract_at_stations(data, stations, run_time)


## upsert_forecasts(records)
DatabaseRepository.ingest_forecasts(records)

# run_once(run_time)
# │
# ├── 1. is_run_already_ingested(model, run_time)
# │
# ├── 2. get_active_stations()
# │
# ├── 3. download_grib(url, tmp_path)
# │
# ├── 4. open_and_group_datasets(tmp_path)
# │
# ├── 5. extract_at_stations(grouped_datasets, stations)
# │
# ├── 6. mark_forecast_run(model, run_time, 'running')
# │
# ├── 7. upsert_forecasts(records)
# │
# └── 8. mark_forecast_run(model, run_time, 'success', n_rows)
#          └── on failure → mark_forecast_run(model, run_time, 'failed')














