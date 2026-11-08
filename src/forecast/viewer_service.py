"""
This is the service layer for the weather viewer page.
Its job is to orchestrate all the steps needed to build
the full response the frontend expects when a user clicks
a location on the map.

It knows about:
- What data to fetch and in what order
- How to transform raw DB rows into frontend-friendly shapes
- What the final response structure looks like

"""

import copy
import logging
from datetime import datetime, timedelta

from src import time_utils
from src.data import queries
from src.forecast.activities.activity_recommendations import build_activity
from src.forecast.presentation import (
    build_daily_forecast,
    build_hourly_forecast,
)
from src.geo.spatial import get_nearest_station
from src.forecast.widgets import build_weather_widgets

logger = logging.getLogger(__name__)

VIEWER_ACTIVITIES = (
    "cycling",
    "running",
    "hiking",
    "picnic",
    "stargazing",
    "gardening",
    "clothing",
    "driving",
)


def get_viewer_data(lat: float, lng: float) -> dict:
    """
    Main entry point called by the API layer.
    Receives coordinates, returns the full response dict
    shaped exactly like mockWeatherDetails on the frontend.
    """

    # Step 1   find the nearest station to the clicked location
    nearest_station = get_nearest_station(lat, lng)
    logger.info(f"Nearest station found: {nearest_station.station_id} - {nearest_station.location_name}")

    # Step 2   get current time truncated to the hour
    # This is used to fetch the current observation and forecast from now onward
    current_time = time_utils.current_utc_iso("hour")
    today = time_utils.current_france_date_iso()

    current_obs = queries.get_observations_at(
        nearest_station.station_id, current_time
    )
    today_obs = queries.get_observations_for_day(nearest_station.station_id, today)
    forecast = queries.get_forecasts_after(nearest_station.station_id, current_time)
    today_forecast = queries.get_forecasts_for_day(
        nearest_station.station_id, today
    )

    station_info = nearest_station.__dict__

    return _build_response(station_info, current_obs, today_obs, forecast, today_forecast)

def validate_and_complete_current_obs(current_obs: list[dict], forecast: list[dict]) -> dict:
    def modify_time_step_fr_if_necessary(time_step: str) -> str:
        dt = datetime.fromisoformat(time_step.replace('Z', '+00:00'))
        one_hour_ago = dt - timedelta(hours=1)
        one_hour_ago  = one_hour_ago.isoformat().replace('+00:00', 'Z')
        return one_hour_ago  
        
    if current_obs is None or current_obs == [] or len(current_obs)>1:
        current_obs = copy.deepcopy(forecast[0])
        current_time_step = modify_time_step_fr_if_necessary(time_step = current_obs["time_step_fr"])
        current_obs["time_step_fr"] = current_time_step
        return current_obs
    
    current_obs = current_obs[0]
    variables_to_check = ["temperature_celsius", "humidity_percentage", 
                          "wind_speed_m_per_s", "precipitation_mm", "snow_precipitation_mm",
                          "mean_sea_level_pressure", "wind_gust_m_per_s", "cape_m2_s2",
                          "total_cloud_cover"]

    for variable in variables_to_check :
        if variable not in current_obs.keys() or current_obs[variable] is None:
            current_obs[variable] = forecast[0][variable]
    return current_obs
    

def _build_response(station_info: dict, current_obs: list[dict], today_obs: list[dict], forecast: list[dict], today_forecast: list[dict]) -> dict:
    """
    Takes station and weather data and transforms it into the exact shape the
    frontend expects.

    raw_data shape coming in:
    {
        "station_info": {...},
        "forecast": [{...}, ...]
    }

    Response shape going out matches mockWeatherDetails + mockForecast
    structure on the frontend.
    """
    # The first forecast entry represents current/next conditions
    # current = forecast[0] if forecast else {}
    current_obs = validate_and_complete_current_obs(current_obs, forecast)
    
    return {
        "station":    _build_station(station_info),
        # "conditions": _build_conditions(current),
        "forecast":   build_hourly_forecast(current_obs, forecast),
        "daily":      build_daily_forecast(today_obs, forecast, today_forecast),
        "widgets":    build_weather_widgets(current_obs, forecast),
        "activities": _build_lifestyle(current_obs, forecast)
    }


def _build_station(station_info: dict) -> dict:
    return {
        "location_name": station_info.get("location_name", "Unknown"),
        "lat":      station_info.get("latitude"),
        "lng":     station_info.get("longitude"),
    }

def _build_lifestyle(current: dict, forecast: list[dict]) -> list:
    """
    Builds all activities. Each activity builder receives current conditions
    for the summary card and the full forecast for hourly timeline and
    best window computation.
    """
    return [
        build_activity(current, forecast, activity)
        for activity in VIEWER_ACTIVITIES
    ]
