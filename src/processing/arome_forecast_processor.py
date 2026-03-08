from dataclasses import asdict
import os
import numpy as np
import pandas as pd
import cfgrib
import xarray as xr
import tempfile
from src.processing.spatial import extract_at_indices, find_nearest_grid_indices
from src.data.models import BronzeForecastRecords
from src.data.repository import DatabaseRepository
import logging
# from src.processing.grib_grouping_rules import GroupingRule

logger = logging.getLogger(__name__)

class GribProcessor:
    def __init__(self, grib_bytes: bytes, run_time : str):
        self.grib_bytes = grib_bytes
        self.run_time = run_time

    def load(self) -> dict[str, xr.Dataset]:
        tmp = tempfile.NamedTemporaryFile(suffix=".grib2", delete=False)
        try:
            tmp.write(self.grib_bytes)
            tmp.close()

            self.datasets = cfgrib.open_datasets(tmp.name)
        finally:
            pass
            # os.remove(tmp.name)
    
    def get_ready_to_ingest_records(self):
        """
        This is the pipeline of all data transformations needed to get from raw GRIB bytes to station-level records.
        Explanation of the steps:
            1. load() - read GRIB bytes into xarray Datasets using cfgrib.
            2. extract_forecast_variables_data() - flatten the list of Datasets into a dict of variable name → DataArray, filtering only the variables we care about (e.g. those in BronzeForecastRecords).
            3. extract_data_at_stations() - for each variable's DataArray, extract the values at the nearest grid point to each station, resulting in a dict of variable name → (n_stations, n_steps) array.
            4. build_forecast_records() - combine the extracted variable arrays with station metadata and timestamps to build a list of dicts ready for database insertion.
        """
        self.load()
        self.reference_data = next(iter(self.datasets))
        grid_lats = self.reference_data.latitude.values
        grid_lons = self.reference_data.longitude.values

        stations = DatabaseRepository.get_stations()
        
        variables = BronzeForecastRecords.forecast_variables()  # all non-metadata fields
        extracted_data = GribProcessor.extract_forecast_variables_data(self.datasets, variables)
        records = GribProcessor.extract_data_at_stations_records(extracted_data, stations, grid_lats, grid_lons, self.run_time)

        return records

    @staticmethod
    def extract_forecast_variables_data(
        datasets: list[xr.Dataset],
        variables: set[str] = None
    ) -> dict[str, xr.DataArray]:
        """
        Flatten list of datasets into a direct variable-name → DataArray mapping.
        No implicit grouping — every variable is a first-class citizen.
        
        If variables is provided, only extract those (e.g. BronzeForecastRecords columns).
        """
        result = {}

        for ds in datasets:
            for var in ds.data_vars:
                if var in variables:
                    result[var] = ds[var]
        return result
        

    # @staticmethod
    # def extract_data_at_stations_records(
    #     data     : dict[str, xr.DataArray],   # flat dict from GribProcessor
    #     stations : list[dict],
    #     grid_lats : np.ndarray,
    #     grid_lons : np.ndarray,
    #     run_time : str
    # ) -> list[dict]:
        
    #     indices = find_nearest_grid_indices(stations, grid_lats, grid_lons)
    #     # Extract all variables at once
    #     variables_forecasts_at_stations = {var: extract_at_indices(da.values, indices) for var, da in data.items()}

    #     valid_times = next(iter(data.values())).valid_time.values  # assume all variables share the same valid_time dimension
        
    #     valid_times_ts = [pd.Timestamp(vt) for vt in valid_times]
    #     run_time_ts    = pd.Timestamp(run_time)
    #     ingestion_ts   = pd.Timestamp('now', tz='UTC')
    #     station_ids    = [idx.station_id for idx in indices]

    #     import pdb
    #     pdb.set_trace()

    #     records = []
    #     for s_idx, station_id in enumerate(station_ids):
    #         for t_idx, valid_time in enumerate(valid_times_ts):
    #             records.append(BronzeForecastRecords(
    #                 station_id     = station_id,
    #                 run_time       = run_time_ts,
    #                 valid_time     = valid_time,
    #                 ingestion_time = ingestion_ts,
    #                 **{var: float(arr[s_idx, t_idx]) for var, arr in variables_forecasts_at_stations.items()}
    #             ))

    #     return records


    @staticmethod
    def extract_data_at_stations_records(
        data      : dict[str, xr.DataArray],
        stations  : list[dict],
        grid_lats : np.ndarray,
        grid_lons : np.ndarray,
        run_time  : str,
    ) -> list[dict]:

        indices   = find_nearest_grid_indices(stations, grid_lats, grid_lons)
        run_time_ts  = pd.Timestamp(run_time)
        ingestion_ts = pd.Timestamp('now', tz='UTC')
        station_ids  = [idx.station_id for idx in indices]

        # import pdb
        # pdb.set_trace()
        # --- 1. Build per-variable time index ---
        # { var: { pd.Timestamp: array(n_stations,) } }
        var_time_arrays: dict[str, dict[pd.Timestamp, np.ndarray]] = {}

        for var, da in data.items():
            extracted = extract_at_indices(da.values, indices)  # (n_stations, n_steps)
            var_time_arrays[var] = {
                pd.Timestamp(vt): extracted[:, t_idx]
                for t_idx, vt in enumerate(da.valid_time.values)
            }

        # --- 2. Find the union of all valid_times ---
        all_valid_times: set[pd.Timestamp] = set()
        for times in var_time_arrays.values():
            all_valid_times.update(times.keys())

        # --- 3. Warn on misalignments ---
        for var, times in var_time_arrays.items():
            missing = all_valid_times - set(times.keys())
            if missing:
                logger.warning(
                    f"Variable '{var}' missing {len(missing)} timesteps: "
                    f"{sorted(missing)} — will be filled with None"
                )

        # --- 4. Build records over union of times ---
        records = []
        for s_idx, station_id in enumerate(station_ids):
            for valid_time in sorted(all_valid_times):
                records.append(BronzeForecastRecords(
                    station_id     = station_id,
                    run_time       = run_time_ts,
                    valid_time     = valid_time,
                    ingestion_time = ingestion_ts,
                    **{
                        var: float(time_map[valid_time][s_idx])
                            if valid_time in time_map else None
                        for var, time_map in var_time_arrays.items()
                    }
                ))

        return records