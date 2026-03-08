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
from src.data.models import BronzeForecastRecords
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

api= APIFactory.create("meteofrance_forecast_arome", "0025SP1")
client = ForecastAromeClient(api)

ingestor = ForecastIngestor(client)
ingestor.run_once()



reference_time = TimeManager.last_arome_forecast_run_time_iso()

## 2. download_grib(url, tmp_path)
api= APIFactory.create("meteofrance_forecast_arome", "0025SP1")
client = ForecastAromeClient(api)
params = {
    "referencetime": "2026-03-08T15:00:00Z",
    "time": "07H12H",
    "format": "grib2"
}

params = {
    "referencetime": reference_time,
    "time": ["00H06H", "07H12H", "13H18H", "19H24H", "25H30H", "31H36H", "37H42H", "43H48H", "49H51H"],
    "format": "grib2"
}

data = client.fetch_data(params=params)


## 3. get_active_stations()
from src.data.repository import DatabaseRepository
stations = DatabaseRepository.get_stations()

## 4. open_and_group_datasets(tmp_path)
run_time = params["referencetime"]
gribprocessor = GribProcessor(data, stations, run_time)
gribprocessor.load()
records = gribprocessor.get_ready_to_ingest_records()


DatabaseRepository.insert_forecasts(records)





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














