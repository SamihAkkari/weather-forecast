from dataclasses import asdict
import os
import numpy as np
import pandas as pd
import cfgrib
import xarray as xr
import tempfile
from src.processing.spatial import extract_at_indices, find_nearest_grid_indices
# from src.data.models import BronzeObservationRecords
# from src.processing.grib_grouping_rules import GroupingRule

class ObservationProcessor:
    def __init__(self, response_data: list[dict]):
        self.response_data = response_data 

    def get_ready_to_ingest_records(self, records_class):
        records = []
        for observation in self.response_data:
            records.append(records_class(
                **{var: val for var, val in observation.items()}
            ))
        return records