from dataclasses import dataclass, fields as dc_fields
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
class SilverObservationListeStationsRecords(BaseRecord):
    station_id:     str
    department_id:  str
    location_name:  str
    latitude:       float
    longitude:      float
    altitude:       float
    openning_date:  datetime
    station_type:   str
    transfer_time_fr: datetime


@dataclass
class ForecastRecord(BaseRecord):
    """Common behavior for bronze AROME forecast records."""

    _METADATA_FIELDS = frozenset(
        {"station_id", "run_time", "valid_time", "ingestion_time"}
    )

    @classmethod
    def forecast_variables(cls) -> set[str]:
        return {f.name for f in dc_fields(cls) if f.name not in cls._METADATA_FIELDS}


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
    t:              float | None # température sous abri en degrés kelvin
    td:             float | None # dew point temperature measured for the air at 2 metres (about 6.6 feet) above the ground.
    tx:             float | None # température maximale de l'air à 2 mètres au-dessus du sol en degrés kelvin
    tn:             float | None # température minimale de l'air à 2 mètres au-dessus du sol en degrés kelvins
    u:              float | None # humidité relative horaire en %
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
class SP1ForecastAromeRecord(ForecastRecord):
    station_id     : int
    run_time       : datetime # Time when the forecast model was run (e.g. 2026-03-05T12:00:00Z)
    valid_time     : datetime # Time for which the forecast is valid (e.g. 2026-03-05T15:00:00Z)
    t2m            : float  # 2 metre temperature
    r2             : float  # Relative humidity
    si10           : float  # 10 metre wind speed
    wdir10         : float  # 10 metre wind direction
    ssrd           : float  # Surface solar radiation downwards
    tp             : float  # Total precipitation
    prmsl          : float  # Mean sea level pressure (Pa)
    fg10           : float  # Time-maximum 10 metre wind gust (m/s) (represents the absolute highest 3-second wind gust that occurred at a height of 10 meters over the hour timestep)
    tsnowp         : float  # Total snow precipitation (kg/m2) accumulated from the first timestep
    ingestion_time : datetime # Time when the forecast was ingested into the database

@dataclass
class SP2ForecastAromeRecord(ForecastRecord):
    station_id     : int
    run_time       : datetime # Time when the forecast model was run (e.g. 2026-03-05T12:00:00Z)
    valid_time     : datetime # Time for which the forecast is valid (e.g. 2026-03-05T15:00:00Z)
    lcc: float  # low cloud cover (%)
    mcc: float  # medium cloud cover (%)
    hcc: float  # high cloud cover (%)
    CAPE_INS: float  # Convective Available Potential Energy instantaneous (m2/s2)
    ingestion_time : datetime # Time when the forecast was ingested into the database
