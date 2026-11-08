from src.config.config import Config
from src.data.getter import DatabaseGetter
from src.ingestion.time_manager import TimeManager
from src.processing.location_service import get_nearest_station
from src.processing.pv_production import compute_pv_production


def get_pv_production_data(
    lat: float,
    lng: float,
    system_capacity_kw: float,
    inverter_capacity_kw: float,
    tilt: float,
    azimuth: float,
    losses_pct: float = 14.0,
    inverter_efficiency: float = 0.96,
) -> dict:
    nearest_station = get_nearest_station(lat, lng)
    current_time = TimeManager.current_utc_iso("hour")

    forecast_raw, cursor = DatabaseGetter.get_forecasts_at_time_step(
        station_id=nearest_station.station_id,
        fromm=Config.SILVER_FORECAST_AROME_TABLE_NAME,
        time=current_time,
        exactly_at_time=False,
    )
    forecast = DatabaseGetter.transform_data_to_list_of_dict(forecast_raw, cursor)

    if not forecast:
        raise LookupError(
            "No forecast data is available yet for this location. Please try again later."
        )

    return compute_pv_production(
        forecast=forecast,
        lat=lat,
        lng=lng,
        altitude=float(nearest_station.altitude or 0),
        system_capacity_kw=system_capacity_kw,
        inverter_capacity_kw=inverter_capacity_kw,
        tilt=tilt,
        azimuth=azimuth,
        losses_pct=losses_pct,
        inverter_efficiency=inverter_efficiency,
    )
