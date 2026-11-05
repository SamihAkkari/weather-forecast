import logging
from src.data.getter import DatabaseGetter
from src.processing.spatial import find_nearest_station
from src.ingestion.time_manager import TimeManager
from src.config.config import Config
from src.processing.weather_code import compute_hourly_code, compute_daily_code
from datetime import datetime, timedelta
import copy
from src.processing import utils 

logger = logging.getLogger(__name__)

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

VARIABLE_DESCRIPTIONS = {
    "humidity": (
        "Relative humidity indicates the percentage of water vapor in the air. A relative humidity between 40 and 60 percent is"
        "usaully considered comfortable."
    ),
    "feels_like": (
        "The apparent temperature estimates how warm or cold the air feels to a person once humidity and wind "
        "are taken into account: humid air makes warm weather feel hotter, while wind makes it feel cooler. "
        "It is computed with the Steadman formula (used by the Australian Bureau of Meteorology) for a person "
        "in the shade, so direct sunshine, which feels warmer, is not included."
    ),
    "wind": (
        "Mean wind speed over the hour at 10 m above ground, in metres per second (1 m/s = 3.6 km/h). The "
        "direction is where the wind blows from. Gusts, the brief peaks within the hour, can be much stronger than this "
        "mean value."
    ),
    "pressure": (
        "Atmospheric pressure converted to mean sea level, in hectopascals (hPa), so that stations at "
        "different altitudes can be compared. The average is around 1013 hPa; below about 1009 hPa is "
        "usually considered low and above about 1023 hPa high."
    ),
    "sunrise": (
        ""
    ),
}

_DIRECTION_WORDS = {"N": "north", "NE": "north-east", "E": "east", "SE": "south-east",
                    "S": "south", "SW": "south-west", "W": "west", "NW": "north-west"}


def get_viewer_data(lat: float, lng: float) -> dict:
    """
    Main entry point called by the API layer.
    Receives coordinates, returns the full response dict
    shaped exactly like mockWeatherDetails on the frontend.
    """

    # Step 1   find the nearest station to the clicked location
    stations = DatabaseGetter.get_stations()
    nearest_station = find_nearest_station(stations, lat, lng)
    logger.info(f"Nearest station found: {nearest_station.station_id} - {nearest_station.location_name}")

    # Step 2   get current time truncated to the hour
    # This is used to fetch the current observation and forecast from now onward
    # current_time = TimeManager.current_france_time_iso(time_truncation="hour")
    current_time = TimeManager.current_utc_iso("hour")
    # today = str(TimeManager.current_france_time_iso(time_truncation="day"))[:10]
    today = TimeManager.current_france_date_iso()
    
    current_obs_raw, cur = DatabaseGetter.get_observations(station_id=nearest_station.station_id, fromm=Config.OBSERVATIONS_TABLE_NAME_HOURLY, time = current_time)
    current_obs = DatabaseGetter.transform_data_to_list_of_dict(current_obs_raw, cur)
    
    today_obs_raw, cur = DatabaseGetter.get_observations(station_id=nearest_station.station_id, fromm=Config.OBSERVATIONS_TABLE_NAME_HOURLY, time = today )
    today_obs = DatabaseGetter.transform_data_to_list_of_dict(today_obs_raw, cur)
    
    # Fetch only forecast   no observation call
    forecast_raw, cur = DatabaseGetter.get_forecasts_at_time_step(
        station_id=nearest_station.station_id,
        fromm=Config.SILVER_FORECAST_AROME_TABLE_NAME,
        time=current_time,
        exactly_at_time=False
    )
    forecast = DatabaseGetter.transform_data_to_list_of_dict(forecast_raw, cur)

    today_forecast_raw, cur = DatabaseGetter.get_forecasts_for_day(station_id=nearest_station.station_id, fromm=Config.SILVER_FORECAST_AROME_TABLE_NAME, day=today)
    today_forecast = DatabaseGetter.transform_data_to_list_of_dict(today_forecast_raw, cur)

    # forecast = utils.unaccumulate(forecast, "precipitation_mm", nearest_station.station_id)
    # forecast = utils.unaccumulate(forecast, "snow_precipitation_mm", nearest_station.station_id)

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
    Takes the raw data dict from DatabaseGetter and transforms it
    into the exact shape the frontend expects.

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
        "forecast":   _build_hourly_forecast(current_obs, forecast),
        "daily":      _build_daily_forecast(today_obs, forecast, today_forecast),
        "widgets":    _build_widgets(current_obs, forecast),
        "activities": _build_lifestyle(current_obs, forecast)
    }


def _build_station(station_info: dict) -> dict:
    return {
        "location_name": station_info.get("location_name", "Unknown"),
        "lat":      station_info.get("latitude"),
        "lng":     station_info.get("longitude"),
    }

def _build_hourly_forecast(current: dict, forecast: list[dict]) -> list[dict]:
    """
    Builds the hourly cards data   one entry per forecast timestep.
    We limit to 48 hours maximum.
    """
    hourly = [{
        "time_step_fr":  current.get("time_step_fr"),
        "temperature_celsius":   current.get("temperature_celsius"),
        "precipitation_mm": current.get("precipitation_mm"),
        "weather_code": compute_hourly_code(current)
        }]
    
    for entry in forecast[:48]:
        hourly.append(
        {
            "time_step_fr":          entry.get("time_step_fr"),
            "temperature_celsius":   entry.get("temperature_celsius"),
            "precipitation_mm": entry.get("precipitation_mm"),
            "weather_code": compute_hourly_code(entry),
            # "windSpeed":     entry.get("wind_speed_m_per_s"),
            # "humidity":      entry.get("humidity_percentage"),
        })
    return hourly



from datetime import datetime, timedelta


def specify_today_past_hours(today: str) -> list[str]:
    """Return the past hourly timestamps for today that need coverage."""
    # now = TimeManager.current_france_time_iso()
    now = TimeManager.current_utc_iso("hour")
    time_steps = []
    for hour in range(0,23):
        time_stamp = today + "T" + f"{hour:02d}" + ":00:00Z"
        if time_stamp == now:
            break
        time_steps.append(time_stamp )
    return time_steps


def get_past_hours(
    entries: list[dict],
    missing_hours: list[str],
) -> tuple[list[dict], list[str]]:
    """
    Select entries matching missing hourly timestamps.

    Returns the matched entries and the timestamps still missing.
    Entries with a missing temperature do not count as covered.
    """
    indexed = {}

    for entry in entries:
        timestamp = entry.get("time_step_fr")
        if timestamp is None:
            continue

        timestamp = str(timestamp)[:13]

        if entry.get("temperature_celsius") is not None:
            indexed[timestamp] = entry

    remaining = []
    matched = []

    for hour in missing_hours:
        key = str(hour)[:13]

        if key in indexed:
            matched.append(indexed[key])
        else:
            remaining.append(hour)

    return matched, remaining


def discard_last_day_if_not_worth(
    data: list[dict],
    last_day: str,
    minimum_hours: int = 12,
) -> list[dict]:
    """
    Remove the final day's entries if fewer than minimum_hours
    distinct hourly temperatures are available.
    """
    last_day_entries = [
        entry for entry in data
        if str(entry.get("time_step_fr", ""))[:10] == last_day
        and entry.get("temperature_celsius") is not None
    ]

    valid_hours = {
        str(entry["time_step_fr"])[:13]
        for entry in last_day_entries
    }

    if len(valid_hours) < minimum_hours:
        return [
            entry for entry in data
            if str(entry.get("time_step_fr", ""))[:10] != last_day
        ]

    return data


def _build_daily_forecast(today_obs: list[dict], forecast: list[dict], today_forecast: list[dict]) -> list[dict]:
    """
    Aggregates hourly forecast into daily min/max temperature
    and a representative weather condition icon.

    Groups entries by date and computes min/max temp per day.
    The icon is determined by the dominant condition of the day.
    """
    from collections import defaultdict
    
    daily = []
    # today = str(TimeManager.current_france_time_iso(time_truncation="day"))[:10]
    today = TimeManager.current_france_date_iso()
    last_day = forecast[-1]['time_step_fr'][0:10] # careful that it is ordered

    missing_past_hours = specify_today_past_hours(today)

    today_past_hours_observed, missing_past_hours = get_past_hours(today_obs, missing_past_hours)
    forecasted_past_hours, missing_past_hours = get_past_hours(today_forecast, missing_past_hours)
    
    if missing_past_hours:
        logger.warning(
            "Could not fill %d past hourly slots for %s: %s",
            len(missing_past_hours),
            today,
            missing_past_hours,
        )  
    
    data = today_past_hours_observed + forecasted_past_hours + forecast
    
    data = discard_last_day_if_not_worth(data, last_day) # should retrun the data either as it is if more than half the hours of th elast day are present or without any timetep of the last day if less


    days = defaultdict(list)
    for entry in data:
        time_str = entry.get("time_step_fr", "")
        if not time_str:
            continue
        # Extract date part   works for both "2026-04-21T14:00:00" and datetime objects
        # date_key = str(time_str)[:10]
        # date_key = TimeManager.iso_to_france_date(time_str)
        date_key = time_str[0:10]
        days[date_key].append(entry)


    for date_key in sorted(days.keys()):
        entries = days[date_key]
        temps = [
            e.get("temperature_celsius")
            for e in entries
            if e.get("temperature_celsius") is not None
        ]
        if not temps:
            continue

        # Determine day label
        if date_key == today:
            label = "Today"
        else:
            from datetime import datetime
            label = datetime.strptime(date_key, "%Y-%m-%d").strftime("%a %d")

        daily.append({
            "day":  label,
            "min":  round(min(temps), 1),
            "max":  round(max(temps), 1),
            "weather_code": compute_daily_code(entries),
        })

    return daily


def _build_widgets(current, forecast: list[dict]) -> dict:
    """
    Builds the weather widgets data.
    Most values come from current conditions (observations).
    Some are derived from the forecast (UV, visibility, pressure
    if not in observations).

    For now we use conditions for what we have and leave
    derived fields as placeholders   you can enrich these
    as your data model grows.
    """
    temp    = current.get("temperature_celsius") if current and current != 0 else None
    wind    = current.get("wind_speed_m_per_s") if current and current != 0 else None
    wind_dir_degree = current.get("wind_direction_degree") if current and current != 0 else None
    humidity = current.get("humidity_percentage") if current and current != 0 else None
    pressure = current.get("mean_sea_level_pressure") if current and current != 0 else None
    feels   = _compute_feels_like(temp, humidity, wind)
    # precip  = current.get("precipitation_mm") if current and current != 0 else None


    hourly_humidity = [{"time_step_fr": entry.get("time_step_fr"), "value": entry.get("humidity_percentage")} for entry in forecast[:48]]
    # hourly_wind_dir = [{"time_step_fr": entry.get("time_step_fr"), "value": _wind_direction(entry.get("wind_direction_degree"))} for entry in forecast[:48]]
    hourly_wind_speed = [{"time_step_fr": entry.get("time_step_fr"), "value":entry.get("wind_speed_m_per_s"), "gust_value": entry.get("wind_gust_m_per_s")} for entry in forecast[:48]]
    # hourly_pressure = [{"time_step_fr": entry.get("time_step_fr"), "value":round(entry.get("mean_sea_level_pressure")/100, 1)} for entry in forecast[:48]]
    hourly_feels = [{"time_step_fr": entry.get("time_step_fr"), "value":_compute_feels_like(entry.get("temperature_celsius"), entry.get("humidity_percentage"), entry.get("wind_speed_m_per_s"))} for entry in forecast[:48]]

    hourly_pressure = [
        {"time_step_fr": e.get("time_step_fr"),
         "value": round(e["mean_sea_level_pressure"] / 100, 1)
                  if e.get("mean_sea_level_pressure") is not None else None}
        for e in forecast[:48]
    ]


    
    # import pdb
    # pdb.set_trace()
    return {
        "humidity": {
            "value":   round(humidity, 1) if humidity is not None else None,
            "unit":    "%",
            "message": _humidity_message(humidity),
            "variable_description": VARIABLE_DESCRIPTIONS["humidity"],
            "hourly_values": hourly_humidity 
        },
        "feels_like": {
            "value":   feels,
            "unit":    "°C",
            "message": _feels_like_message(temp, feels),
            "variable_description": VARIABLE_DESCRIPTIONS["feels_like"],
            "hourly_values": hourly_feels
        },
        "wind": {
            "value":     round(wind, 1) if wind is not None else None,
            "unit":      "m/s",
            "direction": _wind_direction(wind_dir_degree),
            "message":   _wind_message(wind),
            "variable_description":  VARIABLE_DESCRIPTIONS["wind"],
            "hourly_values": hourly_wind_speed 
        },
        "sunrise": {
            "value":   "N/A",   # TODO: compute from lat/lng using astral library
            "unit":    "",
            "message": "Sunrise data coming soon",
        },
        "uv_index": {
            "value":   "N/A",       # TODO: add UV index when available in DB
            "unit":    "",
            "message": "uv_index data coming soon",
        },
        "visibility": {
            "value":   "N/A",      # TODO: add visibility when available in DB
            "unit":    "",
            "message": "visibility data coming soon",
        },
        "pressure": {
            "value":   round(pressure/100, 1)
                       if current and current != 0 and pressure
                       else None,
            "unit":    "hPa",
            "message": "",
            "variable_description": VARIABLE_DESCRIPTIONS["pressure"],
            "hourly_values": hourly_pressure
        },
    }

def _build_lifestyle(current: dict, forecast: list[dict]) -> list:
    """
    Builds all activities. Each activity builder receives current conditions
    for the summary card and the full forecast for hourly timeline and
    best window computation.
    """
    return [
        utils._build_activity(current, forecast, "cycling"),
        utils._build_activity(current, forecast, "running"),
        utils._build_activity(current, forecast, "hiking"),
        utils._build_activity(current, forecast, "picnic"),
        # utils._build_activity(current, forecast, "fishing"),
        # utils._build_activity(current, forecast, "photography"),
        utils._build_activity(current, forecast, "stargazing"),
        utils._build_activity(current, forecast, "gardening"),
        utils._build_activity(current, forecast, "clothing"),
        utils._build_activity(current, forecast, "driving"),
        # utils._build_activity(current, forecast, "dogwalking"),
    ]

# ── Insight message helpers ────────────────────────────────────────────────────
# Each helper returns a short human-readable sentence based on the value.
# These are pure functions   easy to test and extend.

import math

def _wind_direction(degrees):
    if degrees is None:
        return None
    directions = ["N", "NE", "E", "SE",
                  "S", "SW", "W", "NW"]
    k = math.floor((degrees % 360 + 22.5) / 45) % 8
    return directions[k]

def _compute_feels_like(temp, humidity, wind) -> float | None:
    """
    Calculates apparent temperature using the Bureau of Meteorology
    Steadman approach.

    Inputs:
        temperature_celsius: °C
        humidity_percentage: %
        wind_speed_m_per_s: m/s

    Assumes outdoor conditions in the shade; direct solar radiation
    is not included.
    """

    if temp is None or humidity is None or wind is None:
        return None

    if not all(math.isfinite(v) for v in (temp, humidity, wind)):
        return None

    if not 0 <= humidity <= 100 or wind < 0:
        return None

    # Water vapour pressure (hPa), derived from temperature and RH.
    vapour_pressure = (
        (humidity / 100)
        * 6.105
        * math.exp((17.27 * temp) / (237.7 + temp))
    )

    # Steadman apparent temperature (°C); wind speed is in m/s.
    apparent_temp = (
        temp
        + 0.33 * vapour_pressure
        - 0.70 * wind
        - 4.0
    )

    return round(apparent_temp, 1)


def _humidity_message(humidity: float | None) -> str:
    if humidity is None:
        return "No data"

    if not 0 <= humidity <= 100:
        return "No data"

    if humidity < 30:
        return "Low relative humidity"
    elif humidity <= 60:
        return "Moderate relative humidity"
    elif humidity <= 80:
        return "High relative humidity"
    return "Very high relative humidity"


def _feels_like_message(
    temp: float | None,
    feels: float | None,
) -> str:
    """Describe the difference between air and apparent temperature."""
    if temp is None or feels is None:
        return "No data"

    if not math.isfinite(temp) or not math.isfinite(feels):
        return "No data"

    diff = feels - temp

    if diff <= -3:
        return "Feels significantly colder"
    elif diff < -1:
        return "Feels slightly colder"
    elif diff >= 3:
        return "Feels significantly warmer"
    elif diff > 1:
        return "Feels slightly warmer"

    return "Feels similar to the air temperature"

def _wind_message(wind: float | None) -> str:
    """
    Describe forecast wind speed in metres per second uisng Beaufort Wind Scale.
    https://www.weather.gov/mfl/beaufort
    """
    if wind is None:
        return "No data"

    if not math.isfinite(wind) or wind < 0:
        return "No data"

    if wind < 0.3:
        return "Calm"
    elif wind < 1.6:
        return "Light air"
    elif wind < 3.4:
        return "Light breeze"
    elif wind < 5.5:
        return "Gentle breeze"
    elif wind < 8.0:
        return "Moderate breeze"
    elif wind < 10.8:
        return "Fresh breeze"
    elif wind < 13.9:
        return "Strong breeze"
    elif wind < 17.2:
        return "Near gale"
    elif wind < 20.8:
        return "Gale"
    elif wind < 24.5:
        return "Strong gale"
    elif wind < 28.5:
        return "Storm"
    elif wind < 32.7:
        return "Violent storm"

    return "Hurricane-force winds"


# "id":      "stargazing",
# "icon":    "🔭",
# "id":      "jacket",
# "icon":    "🧥",
# "id":      "photography",
# "icon":    "📷",
# "id":      "gardening",
# "icon":    "🌱",
