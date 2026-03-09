from dataclasses import dataclass, field, fields as dc_fields
from typing import Callable, Optional, Type
from datetime import datetime


@dataclass
class BaseRecord:
    """Mixin providing introspection utilities for all record dataclasses."""

    @classmethod
    def columns(cls) -> list[str]:
        return [f.name for f in dc_fields(cls)]

    def values(self) -> list:
        return [getattr(self, f.name) for f in dc_fields(self)]


@dataclass
class ObservationListeStationsRecords(BaseRecord):
    station_id:     int
    department_id:  int
    name:           str
    latitude:       float
    longitude:      float
    altitude:       float
    openning_date:  str
    pack:           str


@dataclass
class ObservationInfrahoraire6mRecord(BaseRecord):
    lat:            float
    lon:            float
    geo_id_insee:   str
    reference_time: datetime
    insert_time:    datetime
    validity_time:  datetime
    t:              float | None
    td:             float | None
    u:              float | None
    dd:             float | None
    ff:             float | None
    dxi10:          float | None
    fxi10:          float | None
    rr_per:         float | None
    t_10           : float | None
    t_20           : float | None
    t_50           : float | None
    t_100          : float | None
    vv             : float | None
    etat_sol       : float | None
    sss            : float | None
    insolh         : float | None
    ray_glo01      : float | None
    pres           : float | None
    pmer           : float | None


@dataclass
class ObservationHoraireRecord(BaseRecord):
    lat:            float
    lon:            float
    geo_id_insee:   str
    reference_time: datetime
    insert_time:    datetime
    validity_time:  datetime
    t:              float | None
    td:             float | None
    tx:             float | None
    tn:             float | None
    u:              float | None
    ux:             float | None
    un:             float | None
    dd:             float | None
    ff:             float | None
    dxy:            float | None
    fxy:            float | None
    dxi:            float | None
    fxi:            float | None
    rr1:            float | None  # Precipitation in the last hour (mm)
    t_10:           float | None
    t_20:           float | None
    t_50:           float | None
    t_100:          float | None
    vv:             float | None
    etat_sol:       float | None
    sss:            float | None
    n:              float | None
    insolh:         float | None
    ray_glo01:      float | None
    pres:           float | None
    pmer:           float | None


@dataclass
class ForecastAromeRecord(BaseRecord):
    station_id     : int
    run_time       : datetime # Time when the forecast model was run (e.g. 2026-03-05T12:00:00Z)
    valid_time     : datetime # Time for which the forecast is valid (e.g. 2026-03-05T15:00:00Z)
    t2m            : float  # 2 metre temperature
    r2             : float  # Relative humidity
    si10           : float  # 10 metre wind speed
    wdir10         : float  # 10 metre wind direction
    ssrd           : float  # Surface solar radiation downwards
    tp             : float  # Total precipitation
    ingestion_time : datetime # Time when the forecast was ingested into the database


    _METADATA_FIELDS = {'station_id', 'run_time', 'valid_time', 'ingestion_time'}

    @classmethod
    def forecast_variables(cls) -> set[str]:
        return {f.name for f in dc_fields(cls) if f.name not in cls._METADATA_FIELDS}

    # @classmethod
    # def variables_2m(cls) -> set[str]:
    #     return {f.name for f in fields(cls) if f.name in {'t2m', 'r2'}}

    # @classmethod
    # def variables_10m(cls) -> set[str]:
    #     return {f.name for f in fields(cls) if f.name in {'si10', 'wdir10'}}

    # @classmethod
    # def variables_accumulation(cls) -> set[str]:
    #     return {f.name for f in fields(cls) if f.name in {'ssrd', 'tp'}}

























