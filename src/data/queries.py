import time
from datetime import date, datetime, timedelta

from src.config.config import Config
from src.data.db import fetch_dicts
from src.data.models import SilverObservationListeStationsRecords as Station

_STATIONS = f"{Config.SILVER_SCHEMA}.{Config.STATIONS_TABLE_NAME}"
_OBSERVATIONS = f"{Config.SILVER_SCHEMA}.{Config.OBSERVATIONS_TABLE_NAME_HOURLY}"
_FORECASTS = f"{Config.SILVER_SCHEMA}.{Config.SILVER_FORECAST_AROME_TABLE_NAME}"

_STATIONS_TTL_SECONDS = 3600
_stations_cache: tuple[float, list[Station]] | None = None


def _day_bounds(day: str) -> tuple[datetime, datetime]:
    """Return the start and end of an ISO calendar day."""
    start = datetime.combine(date.fromisoformat(day), datetime.min.time())
    return start, start + timedelta(days=1)


def _iso_strings(rows: list[dict]) -> list[dict]:
    """Serialize datetimes for the presentation layer."""
    for row in rows:
        for key, value in row.items():
            if isinstance(value, datetime):
                row[key] = value.isoformat()
    return rows


def _latest_forecasts(station_id: str, condition: str, *params) -> list[dict]:
    """Fetch forecasts, keeping the latest model run for each timestep."""
    sql = f"""
        SELECT DISTINCT ON (station_id, time_step_fr) *
        FROM {_FORECASTS}
        WHERE station_id = %s AND {condition}
        ORDER BY station_id, time_step_fr, run_time DESC
    """
    return _iso_strings(fetch_dicts(sql, (station_id, *params)))


def get_observations_at(station_id: str, timestamp: str) -> list[dict]:
    sql = f"""
        SELECT *
        FROM {_OBSERVATIONS}
        WHERE station_id = %s AND time_step_fr = %s
    """
    return _iso_strings(fetch_dicts(sql, (station_id, timestamp)))


def get_observations_for_day(station_id: str, day: str) -> list[dict]:
    start, end = _day_bounds(day)
    sql = f"""
        SELECT *
        FROM {_OBSERVATIONS}
        WHERE station_id = %s AND time_step_fr >= %s AND time_step_fr < %s
    """
    return _iso_strings(fetch_dicts(sql, (station_id, start, end)))


def get_forecasts_after(station_id: str, after: str) -> list[dict]:
    return _latest_forecasts(station_id, "time_step_fr > %s", after)


def get_forecasts_for_day(station_id: str, day: str) -> list[dict]:
    start, end = _day_bounds(day)
    return _latest_forecasts(
        station_id, "time_step_fr >= %s AND time_step_fr < %s", start, end
    )


def get_stations() -> list[Station]:
    """Stations rarely change, so cache them in memory for an hour."""
    global _stations_cache
    now = time.monotonic()
    if (
        _stations_cache is not None
        and now - _stations_cache[0] < _STATIONS_TTL_SECONDS
    ):
        return _stations_cache[1]

    stations = _load_stations()
    _stations_cache = (now, stations)
    return stations


def _load_stations() -> list[Station]:
    columns = ", ".join(Station.columns())
    rows = fetch_dicts(f"SELECT {columns} FROM {_STATIONS} ORDER BY station_id")
    return [Station(**row) for row in rows]
