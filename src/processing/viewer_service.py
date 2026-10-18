import logging
from src.data.getter import DatabaseGetter
from src.processing.spatial import find_nearest_station
from src.ingestion.time_manager import TimeManager
from src.config.config import Config
from src.processing.weather_code import compute_hourly_code, compute_daily_code

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

It does NOT know about:
- HTTP requests or responses (that's the API layer)
- SQL queries (that's DatabaseGetter)
"""



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
        "lifestyle":  _build_lifestyle(current, forecast),
    }


def _build_station(station_info: dict) -> dict:
    return {
        "location_name": station_info.get("location_name", "Unknown"),
        "lat":      station_info.get("latitude"),
        "lng":     station_info.get("longitude"),
    }


# def _build_conditions(current: dict) -> dict:
#     """
#     Now reads from the first forecast timestep instead of observations.
#     Keys match what silver.forecast exposes after the dbt transformation.
#     """
#     return {
#         "temperature_celsius": current.get("temperature_celsius"),
#         "humidity_percentage": current.get("humidity_percentage"),
#         "wind_speed_m_per_s":  current.get("wind_speed_m_per_s"),
#         "precipitation_mm":    current.get("precipitation_mm"),
#     }

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


# def _pick_daily_icon(entries: list[dict]) -> str:
#     """
#     Picks a representative daily weather icon using
#     daily accumulated precipitation and average cloud cover.
#     Returns a key supported by the frontend ICONS dict.
#     """
#     total_precip = sum(
#         e.get("precipitation_mm") or 0
#         for e in entries
#     )
#     avg_cloud_cover = sum(
#         e.get("total_cloud_cover") or 0
#         for e in entries
#     ) / max(len(entries), 1)

#     if total_precip is None:
#             return "unknown"

#     if total_precip >= 2.0:
#         return "rainy"

#     if avg_cloud_cover is None:
#         return "unknown"

#     if avg_cloud_cover <= 20:
#         return "sunny"
#     elif avg_cloud_cover <= 70:
#         return "partly_cloudy"
#     return "cloudy"


# def _pick_hourly_icon(
#     precipitation_mm: float | None,
#     total_cloud_cover: float | None,
# ) -> str:
#     # Missing precipitation should not be treated as dry weather.
#     if precipitation_mm is None:
#         return "unknown"

#     # Hourly accumulated precipitation: practical starting threshold.
#     if precipitation_mm >= 0.2:
#         return "rainy"

#     if total_cloud_cover is None:
#         return "unknown"

#     if total_cloud_cover <= 20:
#         return "sunny"
#     elif total_cloud_cover <= 70:
#         return "partly_cloudy"
#     else:
#         return "cloudy"



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


def _build_lifestyle(current, forecast: list[dict]) -> dict:
    """
    Builds the lifestyle widget data.
    Each activity is evaluated based on current current and forecast.
    Returns the same shape as mockLifestyle on the frontend.
    """
    temp    = current.get("temperature_celsius") if current and current != 0 else None
    wind    = current.get("wind_speed_m_per_s")  if current and current != 0 else None
    precip  = current.get("precipitation_mm")    if current and current != 0 else None
    humidity = current.get("humidity_percentage") if current and current != 0 else None

    # Total rain in next 6 hours
    rain_next_6h = sum(
        e.get("precipitation_mm") or 0
        for e in forecast[:6]
    )

    def status(good_cond, poor_cond):
        """Helper: returns 'good', 'poor', or 'fair' based on conditions."""
        if poor_cond: return "poor"
        if good_cond: return "good"
        return "fair"

    return {
        "activities": [
            {
                "id":      "running",
                "icon":    "🏃",
                "label":   "Running",
                "status":  status(
                    good_cond = temp and 8 <= temp <= 20 and (wind or 0) < 10 and rain_next_6h < 0.5,
                    poor_cond = (wind or 0) > 15 or rain_next_6h > 2
                ),
                "message": _running_message(temp, wind, rain_next_6h),
            },
            {
                "id":      "cycling",
                "icon":    "🚴",
                "label":   "Cycling",
                "status":  status(
                    good_cond = temp and 10 <= temp <= 25 and (wind or 0) < 8 and rain_next_6h < 0.5,
                    poor_cond = (wind or 0) > 12 or rain_next_6h > 1
                ),
                "message": _cycling_message(wind, rain_next_6h),
            },
            {
                "id":      "fishing",
                "icon":    "🎣",
                "label":   "Fishing",
                "status":  status(
                    good_cond = rain_next_6h < 0.5 and (wind or 0) < 8,
                    poor_cond = (wind or 0) > 15 or rain_next_6h > 3
                ),
                "message": _fishing_message(wind, rain_next_6h),
            },
            {
                "id":      "stargazing",
                "icon":    "🔭",
                "label":   "Stargazing",
                "status":  status(
                    good_cond = rain_next_6h == 0 and (humidity or 100) < 70,
                    poor_cond = rain_next_6h > 0.5 or (humidity or 0) > 85
                ),
                "message": _stargazing_message(rain_next_6h, humidity),
            },
            {
                "id":      "picnic",
                "icon":    "🧺",
                "label":   "Picnic",
                "status":  status(
                    good_cond = temp and temp > 15 and rain_next_6h < 0.5 and (wind or 0) < 10,
                    poor_cond = rain_next_6h > 1 or (temp and temp < 10)
                ),
                "message": _picnic_message(temp, rain_next_6h),
            },
            {
                "id":      "jacket",
                "icon":    "🧥",
                "label":   "Clothing",
                "status":  status(
                    good_cond = temp and temp > 18,
                    poor_cond = temp and temp < 8
                ),
                "message": _clothing_message(temp, rain_next_6h, wind),
            },
            {
                "id":      "photography",
                "icon":    "📷",
                "label":   "Photography",
                "status":  status(
                    good_cond = rain_next_6h < 0.5,
                    poor_cond = rain_next_6h > 2
                ),
                "message": _photography_message(rain_next_6h),
            },
            {
                "id":      "gardening",
                "icon":    "🌱",
                "label":   "Gardening",
                "status":  status(
                    good_cond = temp and 10 <= temp <= 25 and rain_next_6h < 1,
                    poor_cond = rain_next_6h > 3 or (temp and temp < 5)
                ),
                "message": _gardening_message(temp, rain_next_6h),
            },
        ]
    }


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

# def _pressure_message(pressure):
#     if pressure is None: return "No data"
#     if pressure > 1020:  return "High pressure — stable, clear weather likely"
#     if pressure > 1010:  return "Normal pressure conditions"
#     if pressure > 1000:  return "Slightly low — some cloud cover possible"
#     return "Low pressure — unsettled weather likely"

def _running_message(temp, wind, rain):
    if rain > 2:              return "Rainy — not ideal for running"
    if wind and wind > 15:    return "Too windy for a comfortable run"
    if temp and temp < 5:     return "Very cold — dress in layers"
    if temp and 10 <= temp <= 20: return "Perfect conditions for a run"
    return "Acceptable conditions for running"

def _cycling_message(wind, rain):
    if rain > 1:           return "Rain expected — slippery roads"
    if wind and wind > 12: return "Strong headwind likely"
    return "Manageable conditions for cycling"

def _fishing_message(wind, rain):
    if wind and wind > 15: return "Too windy for fishing"
    if rain > 3:           return "Heavy rain — poor fishing conditions"
    return "Calm conditions — decent for fishing"

def _stargazing_message(rain, humidity):
    if rain > 0.5:            return "Cloudy or rainy — poor visibility"
    if humidity and humidity > 85: return "High humidity may obscure the sky"
    return "Fair stargazing conditions tonight"

def _picnic_message(temp, rain):
    if rain > 1:           return "Rain expected — not ideal for a picnic"
    if temp and temp < 10: return "Too cold for a comfortable picnic"
    if temp and temp > 15: return "Great weather for a picnic"
    return "Acceptable conditions for a picnic"

def _clothing_message(temp, rain, wind):
    if temp is None: return "No data"
    if rain > 1:           return "Bring a raincoat"
    if temp < 5:           return "Heavy coat needed"
    if temp < 12:          return "Warm jacket recommended"
    if temp < 18:          return "Light jacket recommended"
    if wind and wind > 10: return "Windbreaker would help"
    return "No jacket needed — comfortable outside"

def _photography_message(rain):
    if rain > 2:   return "Rain will affect your shots"
    if rain > 0.5: return "Overcast light — soft shadows"
    return "Good light conditions for photography"

def _gardening_message(temp, rain):
    if rain > 3:           return "Too much rain — wait for it to pass"
    if temp and temp < 5:  return "Too cold for gardening"
    if rain > 0.5:         return "Light rain — natural watering happening"
    return "Good day for gardening"