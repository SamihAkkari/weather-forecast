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

# !!! These thresholds need to be better calibrated !!!
RULES = {
    "cycling": {
        "temperature": [
            (0, 0.1, "red", "Freezing: risk of icy roads"),
            (5, 0.4, "yellow", "Very cold: dress in layers"),
            (22, 0.9, "green", "Comfortable cycling temperature"),
            (25, 0.5, "yellow", "Warm: stay hydrated"),
            (float("inf"), 0.1, "red", "Too hot: increased risk of overheating"),
        ],

        # Wind speed in km/h
        "wind": [
            (4.16, 0.9, "green", "Light wind: good cycling conditions"),
            (8.3, 0.4, "yellow", "Moderate wind: increased effort and crosswind exposure"),
            (float("inf"), 0.1, "red", "Strong wind: difficult handling, especially in gusts"),
        ],

        # Rainfall intensity in mm/h
        "rain": [
            (0.05, 0.9, "green", "Dry conditions"),
            (0.2, 0.8, "green", "Dry conditions or negligible rainfall"),
            (2.5, 0.4, "yellow", "Rain: reduced grip and longer braking distances"),
            (float("inf"), 0.1, "red", "Heavy rain: poor visibility and hazardous road conditions"),
        ],

        # Snowfall precipitation in mm/h, expressed as water equivalent
        "snow": [
            (0.1, 0.9, "green", "No significant snowfall"),
            (0.5, 0.2, "red", "Light snow: slippery surfaces"),
            (float("inf"), 0.1, "red", "Snowfall: increased risk of poor visibility and icy roads"),
        ],
    },

    "fishing": {
        "temperature": [
            (0, 0.1, "red", "Freezing: cold exposure and possible icy access"),
            (8, 0.4, "yellow", "Cold: dress warmly and prepare for prolonged exposure"),
            (24, 0.9, "green", "Comfortable air temperature for a fishing session"),
            (30, 0.5, "yellow", "Warm: bring water, shade, and sun protection"),
            (float("inf"), 0.1, "red", "Extreme heat: increased risk of heat stress"),
        ],

        # Wind speed in km/h
        "wind": [
            (2.7, 0.7, "green", "Light wind: comfortable casting conditions"),
            (6.1, 0.9, "green", "Moderate wind: surface chop may favor feeding activity"),
            (9.7, 0.4, "yellow", "Strong wind: difficult casting and reduced control"),
            (float("inf"), 0.1, "red", "Very strong wind: potentially dangerous fishing conditions"),
        ],

        # Precipitation intensity in mm/h
        "rain": [
            (0.1, 0.7, "green", "Dry conditions or negligible rainfall"),
            (1.0, 0.9, "green", "Light rain: potentially favorable low-light conditions"),
            (3.0, 0.5, "yellow", "Moderate rain: reduced comfort and visibility"),
            (float("inf"), 0.1, "red", "Heavy rain: poor visibility and potentially hazardous conditions"),
        ],
    },

    "picnic": {
        # Currenlty we use the air temeptaure and not the apparent one
        "temperature": [
            (10, 0.1, "red", "Too cold: uncomfortable for an outdoor picnic"),
            (14, 0.4, "yellow", "Cool: warm clothing and blankets recommended"),
            (18, 0.7, "green", "Mild: generally pleasant picnic conditions"),
            (24, 0.9, "green", "Ideal temperature: comfortable outdoor conditions"),
            (29, 0.5, "yellow", "Warm: seek shade and keep food properly chilled"),
            (34, 0.2, "red", "Very hot: risk of heat discomfort and food spoilage"),
            (float("inf"), 0.1, "red", "Extreme heat: outdoor picnic not recommended"),
        ],

        # Wind speed in km/h
        "wind": [
            (3.3, 0.9, "green", "Light wind: comfortable conditions for a picnic"),
            (4.1, 0.7, "green", "Gentle breeze: generally pleasant outdoors"),
            (7, 0.4, "yellow", "Strong breeze: napkins and lightweight items may blow away"),
            (8.3, 0.2, "red", "Very windy: difficult to keep food and picnic items in place"),
            (float("inf"), 0.1, "red", "Dangerous wind: outdoor picnic not recommended"),
        ],

        # Wind gust speed in km/h
        "wind_gust": [
            (7, 0.9, "green", "Light gusts: picnic items should remain manageable"),
            (11, 0.4, "yellow", "Strong gusts: secure belongings and lightweight equipment"),
            (float("inf"), 0.1, "red", "Dangerous gusts: outdoor picnic not recommended"),
        ],

        # Precipitation intensity in mm/h
        "rain": [
            (0.01, 0.9, "green", "Dry conditions: ideal for keeping food and belongings dry"),
            (0.1, 0.7, "green", "Negligible precipitation: generally suitable conditions"),
            (0.2, 0.5, "yellow", "Light drizzle: bring shelter and protect food"),
            (0.5, 0.3, "yellow", "Persistent drizzle: reduced comfort and damp belongings"),
            (float("inf"), 0.1, "red", "Heavy rain: picnic outdoors not recommended"),
        ],

        # Total cloud cover as a fraction from 0 to 1
        "cloud_cover": [
            (20, 0.5, "yellow", "Mostly clear: limited natural shade on sunny days"),
            (60, 0.9, "green", "Partial cloud cover: pleasant balance of light and shade"),
            (80, 0.7, "green", "Mostly cloudy: comfortable shade, though conditions may feel cooler"),
            (100, 0.5, "yellow", "Overcast: check temperature and the likelihood of rain"),
        ],
    },
}


def get_viewer_data(lat: float, lng: float) -> dict:
    """
    Main entry point called by the API layer.
    Receives coordinates, returns the full response dict
    shaped exactly like mockWeatherDetails on the frontend.
    """

    # Step 1 — find the nearest station to the clicked location
    stations = DatabaseGetter.get_stations()
    nearest_station = find_nearest_station(stations, lat, lng)
    logger.info(f"Nearest station found: {nearest_station.station_id} - {nearest_station.location_name}")

    # Step 2 — get current time truncated to the hour
    # This is used to fetch the current observation and forecast from now onward
    current_time = TimeManager.current_france_time_iso(time_truncation="hour")
    today = str(TimeManager.current_france_time_iso(time_truncation="day"))[:10]
    
    current_obs_raw, cur = DatabaseGetter.get_observations(station_id=nearest_station.station_id, fromm=Config.OBSERVATIONS_TABLE_NAME_HOURLY, time = current_time)
    current_obs = DatabaseGetter.transform_data_to_list_of_dict(current_obs_raw, cur)
    
    today_obs_raw, cur = DatabaseGetter.get_observations(station_id=nearest_station.station_id, fromm=Config.OBSERVATIONS_TABLE_NAME_HOURLY, time = today )
    today_obs = DatabaseGetter.transform_data_to_list_of_dict(today_obs_raw, cur)
    
    # Fetch only forecast — no observation call
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
    Builds the hourly cards data — one entry per forecast timestep.
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
    now = TimeManager.current_france_time_iso()
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
    today = str(TimeManager.current_france_time_iso(time_truncation="day"))[:10]
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
        # Extract date part — works for both "2026-04-21T14:00:00" and datetime objects
        date_key = str(time_str)[:10]
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
    derived fields as placeholders — you can enrich these
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
    hourly_wind_speed = [{"time_step_fr": entry.get("time_step_fr"), "value":entry.get("wind_speed_m_per_s")} for entry in forecast[:48]]
    hourly_pressure = [{"time_step_fr": entry.get("time_step_fr"), "value":round(entry.get("mean_sea_level_pressure")/100, 1)} for entry in forecast[:48]]
    hourly_feels = [{"time_step_fr": entry.get("time_step_fr"), "value":_compute_feels_like(entry.get("temperature_celsius"), entry.get("humidity_percentage"), entry.get("wind_speed_m_per_s"))} for entry in forecast[:48]]
    
    # import pdb
    # pdb.set_trace()
    return {
        "humidity": {
            "value":   round(humidity, 1) if humidity is not None else None,
            "unit":    "%",
            "message": _humidity_message(humidity),
            "variable_description": "blablablab",
            "hourly_values": hourly_humidity 
        },
        "feels_like": {
            "value":   feels,
            "unit":    "°C",
            "message": _feels_like_message(temp, feels),
            "variable_description": "blablablab",
            "hourly_values": hourly_feels
        },
        "wind": {
            "value":     round(wind, 1) if wind is not None else None,
            "unit":      "m/s",
            "direction": _wind_direction(wind_dir_degree),
            "message":   _wind_message(wind),
            "variable_description": "blablablab",
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
            "message": "k",
            "variable_description": "blablablab",
            "hourly_values": hourly_pressure
        },
    }

def evaluate(value, rules):
    for limit, score, status, description in rules:
        if value <= limit:
            return {
                "score": score,
                "status": status,
                "description": description,
            }

def recommend(activity, conditions, time):
    # import pdb
    # pdb.set_trace()
    
    statuses = []
    scores = []
    results = {}
    for name, rules in RULES[activity].items():
        if conditions.get(name) is not None and rules:
            # print(name)
            # print(activity)
            # print(conditions[name])
            # print(rules)
            # print(evaluate(conditions[name], rules))
            sub_dict = evaluate(conditions[name], rules)
            results[name]= sub_dict 
            statuses.append(sub_dict["status"])
            scores.append(sub_dict["score"])

    if "red" in statuses:
        status = "red"
    elif "yellow" in statuses:
        status = "yellow"
    else:
        status = "green"

    score = min(scores)

    return {
        "time": time,
        "status": status,
        "score": score,
        "parameters": results,
    }


def get_best_windows(hourly_data):
    best_windows = []
    current_window = []

           
    
    def save_window(window):
        if len(window) < 2:
            return

        best_windows.append({
            "from": window[0]["time"],
            "to": window[-1]["time"],
            "reason": "Calm wind · Dry · Mild temperature", #TODO: automate this
        })

    for entry in hourly_data:
        if entry["status"] == "green" or entry["status"]=="yellow":
            current_window.append(entry)
        else:
            save_window(current_window)
            current_window = []

    # Handle a green window that extends to the last entry
    save_window(current_window)
    
    # Sort by duration, longest first
    best_windows.sort(
        key=lambda w: (
            datetime.fromisoformat(w["to"])
            - datetime.fromisoformat(w["from"])
        ).total_seconds(),
        reverse=True,
    )
    return best_windows[:2]

def _build_lifestyle(current: dict, forecast: list[dict]) -> list:
    """
    Builds all activities. Each activity builder receives current conditions
    for the summary card and the full forecast for hourly timeline and
    best window computation.
    """
    return [
        utils._build_cycling(current, forecast),
        utils._build_running(current, forecast),
        utils._build_hiking(current, forecast),
        utils._build_picnic(current, forecast),
        utils._build_fishing(current, forecast),
        utils._build_photography(current, forecast),
        utils._build_stargazing(current, forecast),
        utils._build_gardening(current, forecast),
        utils._build_clothing(current, forecast),
        utils._build_driving(current, forecast),
        utils._build_dog_walking(current, forecast),
    ]

# def _build_lifestyle(current, forecast: list[dict]) -> dict:
#     """
#     Builds the lifestyle widget data.
#     Each activity is evaluated based on current current and forecast.
#     Returns the same shape as mockLifestyle on the frontend.
#     """
#     temp    = current.get("temperature_celsius") if current and current != 0 else None
#     wind    = current.get("wind_speed_m_per_s")  if current and current != 0 else None
#     wind_gust    = current.get("wind_gust_m_per_s")  if current and current != 0 else None
#     precip  = current.get("precipitation_mm")    if current and current != 0 else None
#     snow_precip = current.get("snow_precipitation_mm")    if current and current != 0 else None
#     humidity = current.get("humidity_percentage") if current and current != 0 else None
#     cloud_cover = current.get("total_cloud_cover") if current and current != 0 else None
#     time = current.get("time_step_fr") if current and current != 0 else None
    
#     cycling_current_recomm = recommend("cycling", {"temperature": temp, "wind": wind, "rain": precip, "snow": snow_precip}, time)
#     cycling_hourly_recomm = [recommend("cycling", {"temperature": i.get("temperature_celsius"), "wind": i.get("wind_speed_m_per_s"), "rain": i.get("precipitation_mm"), "snow": i.get("snow_precipitation_mm")}, i.get("time_step_fr")) for i in forecast[1:24]]
#     cycling_best_window = get_best_windows(cycling_hourly_recomm)

#     fishing_current_recomm = recommend("fishing", {"temperature": temp, "wind": wind, "rain": precip}, time)
#     fishing_hourly_recomm = [recommend("fishing", {"temperature": i.get("temperature_celsius"), "wind": i.get("wind_speed_m_per_s"), "rain": i.get("precipitation_mm")}, i.get("time_step_fr")) for i in forecast[1:24]]
#     fishing_best_window = get_best_windows(fishing_hourly_recomm)

#     picnic_current_recomm = recommend("picnic", {"temperature": temp, "wind": wind, "rain": precip, "wind_gust": wind_gust, "cloud_cover": cloud_cover}, time)
#     picnic_hourly_recomm = [recommend("picnic", {"temperature": i.get("temperature_celsius"), "wind": i.get("wind_speed_m_per_s"), "rain": i.get("precipitation_mm"), "wind_gust": i.get("wind_gust_m_per_s"), "cloud_cover": i.get("total_cloud_cover")}, i.get("time_step_fr")) for i in forecast[1:24]]
#     picnic_best_window = get_best_windows(picnic_hourly_recomm)

#     return [
#             {
#                 "id":      "cycling",
#                 "icon":    "🚴",
#                 "label":   "Cycling",
#                 "status": cycling_current_recomm ["status"],
#                 "current_status": cycling_current_recomm,
#                 "hourly": cycling_hourly_recomm,
#                 "best_window": cycling_best_window 
#             },
#             {
#                 "id":      "fishing",
#                 "icon":    "🎣",
#                 "label":   "Fishing",
#                 "status": fishing_current_recomm ["status"],
#                 "current_status": fishing_current_recomm,
#                 "hourly": fishing_hourly_recomm,
#                 "best_window": fishing_best_window 
#             },
#             {
#                 "id":      "picnic",
#                 "icon":    "🧺",
#                 "label":   "Picnic",
#                 "status": picnic_current_recomm ["status"],
#                 "current_status": picnic_current_recomm,
#                 "hourly": picnic_hourly_recomm,
#                 "best_window": picnic_best_window 
#             }
#         ]

# ── Insight message helpers ────────────────────────────────────────────────────
# Each helper returns a short human-readable sentence based on the value.
# These are pure functions — easy to test and extend.

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
