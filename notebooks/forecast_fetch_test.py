# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 00:39:57 2026

@author: sakkari
"""

import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ForecastAromeClient
from src.processing.arome_forecast_processor import GribProcessor


data_api= APIFactory.create("meteofrance_forecast_arome", "0025SP2")
data_client = ForecastAromeClient(data_api)

# description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1_available_data")
# description_client = ForecastAromeClient(description_api)


params = {
    "referencetime" : "2026-04-18T03:00:00Z",
    "time": ["07H12H"],
    "format": "grib2"
}

response = data_client.fetch_data(params = params)  # your API method

grib_processor = GribProcessor(response, params.get("referencetime"))
grib_processor.load()

records = grib_processor.get_ready_to_ingest_records(data_client.api.record_class)



total points: 4822542
valid points: 3994086
nan ratio: 0.17178823948034044

total points: 4822542
valid points: 3994086
nan ratio: 0.17178823948034044


import cfgrib
datasets = cfgrib.open_datasets("tmp43somx6t.grib2")




import eccodes

filepath = "tmp43somx6t.grib2"

# Step 1: Inventory every message in the file
all_messages = []
with open(filepath, "rb") as f:
    while True:
        msg = eccodes.codes_grib_new_from_file(f)
        if msg is None:
            break
        info = {
            "shortName":   eccodes.codes_get(msg, "shortName"),
            "name":        eccodes.codes_get(msg, "name"),
            "typeOfLevel": eccodes.codes_get(msg, "typeOfLevel"),
            "level":       eccodes.codes_get(msg, "level"),
            "stepRange":   eccodes.codes_get(msg, "stepRange"),
            "gridType":    eccodes.codes_get(msg, "gridType"),
        }
        all_messages.append(info)
        eccodes.codes_release(msg)

print(f"Total messages in file: {len(all_messages)}\n")

# Step 2: Summarize unique variables
from collections import Counter
summary = Counter((m["shortName"], m["typeOfLevel"], m["gridType"]) for m in all_messages)
for (shortName, levelType, gridType), count in sorted(summary.items()):
    print(f"  {shortName:25s}  levelType={levelType:25s}  gridType={gridType:15s}  count={count}")