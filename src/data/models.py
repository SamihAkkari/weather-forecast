from dataclasses import dataclass, fields, asdict
from datetime import datetime


@dataclass
class BronzeForecastRecords:
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

    @classmethod
    def columns(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    def values(self) -> list:
        return [getattr(self, f.name) for f in fields(self)]

    @classmethod
    def forecast_variables(cls) -> set[str]:
        return {f.name for f in fields(cls) if f.name not in {'station_id', 'run_time', 'valid_time', 'ingestion_time'}}

    # @classmethod
    # def variables_2m(cls) -> set[str]:
    #     return {f.name for f in fields(cls) if f.name in {'t2m', 'r2'}}

    # @classmethod
    # def variables_10m(cls) -> set[str]:
    #     return {f.name for f in fields(cls) if f.name in {'si10', 'wdir10'}}

    # @classmethod
    # def variables_accumulation(cls) -> set[str]:
    #     return {f.name for f in fields(cls) if f.name in {'ssrd', 'tp'}}


@dataclass
class BronzeObservationRecords:
    lat            : float
    lon            : float
    geo_id_insee   : str
    reference_time : datetime
    insert_time    : datetime
    validity_time  : datetime
    t              : float | None
    td             : float | None
    u              : float | None
    dd             : float | None
    ff             : float | None
    dxi10          : float | None
    fxi10          : float | None
    rr_per         : float | None
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

    @classmethod
    def columns(cls) -> list[str]:
        return [f.name for f in fields(cls)]

@dataclass
class BronzeStationRecords:
    station_id : int
    department_id : int
    name : str
    latitude   : float
    longitude  : float
    altitude   : float
    openning_date : str
    pack : str

    @classmethod
    def columns(cls) -> list[str]:
        return [f.name for f in fields(cls)]