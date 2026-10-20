import logging
from src.data.getter import DatabaseGetter
from src.processing.spatial import find_nearest_station
from src.ingestion.time_manager import TimeManager
from src.config.config import Config
from src.processing.weather_code import compute_hourly_code, compute_daily_code
from datetime import datetime, timedelta

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
            (0.5, 0.4, "yellow", "Light snow: watch for slippery surfaces"),
            (float("inf"), 0.1, "red", "Snowfall: increased risk of poor visibility and icy roads"),
        ],
    },
    # "running": {
    #     "temperature": [
    #         (0,   0, "red", "Too cold"),
    #         (30,  2, "green", "Suitable temperature"),
    #         (float("inf"), 0, "red", "Too hot"),
    #     ],
    #     "wind": [],
    #     "rain": [],
    #     "snow": [],
    # },
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

    # Fetch only forecast — no observation call
    forecast_raw, cur = DatabaseGetter.get_forecasts_at_time_step(
        station_id=nearest_station.station_id,
        fromm=Config.SILVER_FORECAST_AROME_TABLE_NAME,
        time=current_time,
        exactly_at_time=False
    )
    forecast = DatabaseGetter.transform_data_to_list_of_dict(forecast_raw, cur)

    station_info = nearest_station.__dict__

    return _build_response(station_info, forecast)



def _build_response(station_info: dict, forecast: list[dict]) -> dict:
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
    current = forecast[0] if forecast else {}

    return {
        "station":    _build_station(station_info),
        # "conditions": _build_conditions(current),
        "forecast":   _build_hourly_forecast(forecast),
        "daily":      _build_daily_forecast(forecast),
        "widgets":    _build_widgets(current, forecast),
        "activities": _build_lifestyle(current, forecast)
    }


def _build_station(station_info: dict) -> dict:
    return {
        "location_name": station_info.get("location_name", "Unknown"),
        "lat":      station_info.get("latitude"),
        "lng":     station_info.get("longitude"),
    }

def _build_hourly_forecast(forecast: list[dict]) -> list[dict]:
    """
    Builds the hourly cards data — one entry per forecast timestep.
    We limit to 48 hours maximum.
    """
    return [
        {
            "time_step_fr":          entry.get("time_step_fr"),
            "temperature_celsius":   entry.get("temperature_celsius"),
            "precipitation_mm": entry.get("precipitation_mm"),
            "weather_code": compute_hourly_code(entry),
            # "windSpeed":     entry.get("wind_speed_m_per_s"),
            # "humidity":      entry.get("humidity_percentage"),
        }
        for entry in forecast[:48]
    ]


def _build_daily_forecast(forecast: list[dict]) -> list[dict]:
    """
    Aggregates hourly forecast into daily min/max temperature
    and a representative weather condition icon.

    Groups entries by date and computes min/max temp per day.
    The icon is determined by the dominant condition of the day.
    """
    from collections import defaultdict

    days = defaultdict(list)
    for entry in forecast:
        time_str = entry.get("time_step_fr", "")
        if not time_str:
            continue
        # Extract date part — works for both "2026-04-21T14:00:00" and datetime objects
        date_key = str(time_str)[:10]
        days[date_key].append(entry)

    daily = []
    today = str(TimeManager.current_france_time_iso(time_truncation="day"))[:10]

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
    feels   = _compute_feels_like(current, forecast)
    wind    = current.get("wind_speed_m_per_s") if current and current != 0 else None
    wind_dir_degree = current.get("wind_direction_degree") if current and current != 0 else None
    humidity = current.get("humidity_percentage") if current and current != 0 else None
    pressure = current.get("mean_sea_level_pressure") if current and current != 0 else None
    precip  = current.get("precipitation_mm") if current and current != 0 else None

    return {
        "humidity": {
            "value":   round(humidity, 1) if humidity is not None else None,
            "unit":    "%",
            "message": _humidity_message(humidity),
        },
        "feels_like": {
            "value":   feels,
            "unit":    "°C",
            "message": _feels_like_message(temp, feels),
        },
        "wind": {
            "value":     round(wind, 1) if wind is not None else None,
            "unit":      "m/s",
            "direction": _wind_direction(wind_dir_degree),
            "message":   _wind_message(wind),
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
            "message": None,
        },
    }

def evaluate(value, rules):
    for limit, score, status, description in rules:
        if value < limit:
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


def _build_lifestyle(current, forecast: list[dict]) -> dict:
    """
    Builds the lifestyle widget data.
    Each activity is evaluated based on current current and forecast.
    Returns the same shape as mockLifestyle on the frontend.
    """
    temp    = current.get("temperature_celsius") if current and current != 0 else None
    wind    = current.get("wind_speed_m_per_s")  if current and current != 0 else None
    precip  = current.get("precipitation_mm")    if current and current != 0 else None
    snow_precip = current.get("snow_precipitation_mm")    if current and current != 0 else None
    humidity = current.get("humidity_percentage") if current and current != 0 else None
    time = current.get("time_step_fr") if current and current != 0 else None
    
    cycling_current_recomm = recommend("cycling", {"temperature": temp, "wind": wind, "rain": precip, "snow": snow_precip}, time)
    cycling_hourly_recomm = [recommend("cycling", {"temperature": i.get("temperature_celsius"), "wind": i.get("wind_speed_m_per_s"), "rain": i.get("precipitation_mm"), "snow": i.get("snow_precipitation_mm")}, i.get("time_step_fr")) for i in forecast[1:48]]
    cycling_best_window = get_best_windows(cycling_hourly_recomm)
    
    return [

            {
                "id":      "cycling",
                "icon":    "🚴",
                "label":   "Cycling",
                "current_status": cycling_current_recomm,
                "hourly": cycling_hourly_recomm,
                "best_window": cycling_best_window 


            }
        ]

# ── Insight message helpers ────────────────────────────────────────────────────
# Each helper returns a short human-readable sentence based on the value.
# These are pure functions — easy to test and extend.

import math

def _wind_direction(degrees):
    directions = ["N", "NE", "E", "SE",
                  "S", "SW", "W", "NW"]
    k = math.floor((degrees % 360 + 22.5) / 45) % 8
    return directions[k]

def _compute_feels_like(current: dict, forecast: list[dict] | None = None) -> float | None:
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
    if not current:
        return None

    temp = current.get("temperature_celsius")
    humidity = current.get("humidity_percentage")
    wind = current.get("wind_speed_m_per_s")

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






# def _running_message(temp, wind, rain):
#     if rain > 2:              return "Rainy — not ideal for running"
#     if wind and wind > 15:    return "Too windy for a comfortable run"
#     if temp and temp < 5:     return "Very cold — dress in layers"
#     if temp and 10 <= temp <= 20: return "Perfect conditions for a run"
#     return "Acceptable conditions for running"

# def _cycling_message(wind, rain):
#     if rain > 1:           return "Rain expected — slippery roads"
#     if wind and wind > 12: return "Strong headwind likely"
#     return "Manageable conditions for cycling"

# def _fishing_message(wind, rain):
#     if wind and wind > 15: return "Too windy for fishing"
#     if rain > 3:           return "Heavy rain — poor fishing conditions"
#     return "Calm conditions — decent for fishing"

# def _stargazing_message(rain, humidity):
#     if rain > 0.5:            return "Cloudy or rainy — poor visibility"
#     if humidity and humidity > 85: return "High humidity may obscure the sky"
#     return "Fair stargazing conditions tonight"

# def _picnic_message(temp, rain):
#     if rain > 1:           return "Rain expected — not ideal for a picnic"
#     if temp and temp < 10: return "Too cold for a comfortable picnic"
#     if temp and temp > 15: return "Great weather for a picnic"
#     return "Acceptable conditions for a picnic"

# def _clothing_message(temp, rain, wind):
#     if temp is None: return "No data"
#     if rain > 1:           return "Bring a raincoat"
#     if temp < 5:           return "Heavy coat needed"
#     if temp < 12:          return "Warm jacket recommended"
#     if temp < 18:          return "Light jacket recommended"
#     if wind and wind > 10: return "Windbreaker would help"
#     return "No jacket needed — comfortable outside"

# def _photography_message(rain):
#     if rain > 2:   return "Rain will affect your shots"
#     if rain > 0.5: return "Overcast light — soft shadows"
#     return "Good light conditions for photography"

# def _gardening_message(temp, rain):
#     if rain > 3:           return "Too much rain — wait for it to pass"
#     if temp and temp < 5:  return "Too cold for gardening"
#     if rain > 0.5:         return "Light rain — natural watering happening"
#     return "Good day for gardening"


#  {
#                 "id":      "running",
#                 "icon":    "🏃",
#                 "label":   "Running",
#                 "status":  status(
#                     good_cond = temp and 8 <= temp <= 20 and (wind or 0) < 10 and rain_next_6h < 0.5,
#                     poor_cond = (wind or 0) > 15 or rain_next_6h > 2
#                 ),
#                 "message": _running_message(temp, wind, rain_next_6h),
#             },
#             {
#                 "id":      "fishing",
#                 "icon":    "🎣",
#                 "label":   "Fishing",
#                 "status":  status(
#                     good_cond = rain_next_6h < 0.5 and (wind or 0) < 8,
#                     poor_cond = (wind or 0) > 15 or rain_next_6h > 3
#                 ),
#                 "message": _fishing_message(wind, rain_next_6h),
#             },
#             {
#                 "id":      "stargazing",
#                 "icon":    "🔭",
#                 "label":   "Stargazing",
#                 "status":  status(
#                     good_cond = rain_next_6h == 0 and (humidity or 100) < 70,
#                     poor_cond = rain_next_6h > 0.5 or (humidity or 0) > 85
#                 ),
#                 "message": _stargazing_message(rain_next_6h, humidity),
#             },
#             {
#                 "id":      "picnic",
#                 "icon":    "🧺",
#                 "label":   "Picnic",
#                 "status":  status(
#                     good_cond = temp and temp > 15 and rain_next_6h < 0.5 and (wind or 0) < 10,
#                     poor_cond = rain_next_6h > 1 or (temp and temp < 10)
#                 ),
#                 "message": _picnic_message(temp, rain_next_6h),
#             },
#             {
#                 "id":      "jacket",
#                 "icon":    "🧥",
#                 "label":   "Clothing",
#                 "status":  status(
#                     good_cond = temp and temp > 18,
#                     poor_cond = temp and temp < 8
#                 ),
#                 "message": _clothing_message(temp, rain_next_6h, wind),
#             },
#             {
#                 "id":      "photography",
#                 "icon":    "📷",
#                 "label":   "Photography",
#                 "status":  status(
#                     good_cond = rain_next_6h < 0.5,
#                     poor_cond = rain_next_6h > 2
#                 ),
#                 "message": _photography_message(rain_next_6h),
#             },
#             {
#                 "id":      "gardening",
#                 "icon":    "🌱",
#                 "label":   "Gardening",
#                 "status":  status(
#                     good_cond = temp and 10 <= temp <= 25 and rain_next_6h < 1,
#                     poor_cond = rain_next_6h > 3 or (temp and temp < 5)
#                 ),
#                 "message": _gardening_message(temp, rain_next_6h),
#             },