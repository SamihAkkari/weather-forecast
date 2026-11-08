"""Reference only: full AROME/Météo-France schemas, not used at runtime.

Kept as documentation of the variables the APIs expose; the models in
models.py are the subset the pipeline actually ingests.
"""

from dataclasses import dataclass
from datetime import datetime

from src.data.models import BaseRecord


@dataclass
class BronzeObservationListeStationsRecords(BaseRecord):
    station_id: int
    department_id: int
    name: str
    latitude: float
    longitude: float
    altitude: float
    openning_date: str
    pack: str


@dataclass
class AllSP1ForecastAromeRecords(BaseRecord):
    u10: float
    v10: float
    si10: float
    fg10: float
    efg10: float
    nfg10: float
    wdir10: float
    t2m: float
    r2: float
    prmsl: float
    ssrd: float
    tp: float
    tgrp: float
    tsnowp: float


@dataclass
class AllSP2ForecastAromeRecords(BaseRecord):
    d2m: float
    sh2: float
    mx2t: float
    mn2t: float
    t: float
    sp: float
    blh: float
    lcc: float
    mcc: float
    hcc: float
    tirf: float
    CAPE_INS: float


@dataclass
class SilverForecastAromeRecords(BaseRecord):
    station_id: str
    run_time: datetime
    time_step_fr: datetime
    forecast_step: int
    temperature_celsius: float
    humidity_percentage: float
    wind_direction_degree: float
    wind_speed_m_per_s: float
    CUMUL_precipitation_mm: float
    CUMUL_global_radiation_j_m2: float
    total_cloud_cover: float
    cape_m2_s2: float
    mean_sea_level_pressure: float
    CUMUL_snow_precipitation_mm: float
    wind_gust_m_per_s: float
    transfer_time_fr: datetime
    precipitation_mm: float
    global_radiation_J_m2: float
    snow_precipitation_mm: float
