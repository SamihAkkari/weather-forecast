from src.config import Config
from src.analysis.forecast_analysis import compute_analysis
from src.geo.spatial import get_nearest_station


def get_analysis_data(
    days: int = 7,
    lat: float | None = None,
    lng: float | None = None,
) -> dict:
    station_id = None
    if lat is not None and lng is not None:
        station_id = get_nearest_station(lat, lng).station_id

    return compute_analysis(
        days=days,
        station_id=station_id,
        forecast_table=f"{Config.SILVER_SCHEMA}.{Config.SILVER_FORECAST_AROME_TABLE_NAME}",
        obs_table=f"{Config.SILVER_SCHEMA}.{Config.OBSERVATIONS_TABLE_NAME_HOURLY}",
    )
