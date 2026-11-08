import math


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
    "sunrise": "",
}


def build_weather_widgets(current: dict, forecast: list[dict]) -> dict:
    """Build the current-condition widgets and their hourly values."""
    temp = current.get("temperature_celsius") if current and current != 0 else None
    wind = current.get("wind_speed_m_per_s") if current and current != 0 else None
    wind_direction = (
        current.get("wind_direction_degree") if current and current != 0 else None
    )
    humidity = (
        current.get("humidity_percentage") if current and current != 0 else None
    )
    pressure = (
        current.get("mean_sea_level_pressure") if current and current != 0 else None
    )
    feels_like = _compute_feels_like(temp, humidity, wind)
    forecast_hours = forecast[:48]

    hourly_humidity = [
        {
            "time_step_fr": entry.get("time_step_fr"),
            "value": entry.get("humidity_percentage"),
        }
        for entry in forecast_hours
    ]
    hourly_wind_speed = [
        {
            "time_step_fr": entry.get("time_step_fr"),
            "value": entry.get("wind_speed_m_per_s"),
            "gust_value": entry.get("wind_gust_m_per_s"),
        }
        for entry in forecast_hours
    ]
    hourly_feels_like = [
        {
            "time_step_fr": entry.get("time_step_fr"),
            "value": _compute_feels_like(
                entry.get("temperature_celsius"),
                entry.get("humidity_percentage"),
                entry.get("wind_speed_m_per_s"),
            ),
        }
        for entry in forecast_hours
    ]
    hourly_pressure = [
        {
            "time_step_fr": entry.get("time_step_fr"),
            "value": (
                round(entry["mean_sea_level_pressure"] / 100, 1)
                if entry.get("mean_sea_level_pressure") is not None
                else None
            ),
        }
        for entry in forecast_hours
    ]

    return {
        "humidity": {
            "value": round(humidity, 1) if humidity is not None else None,
            "unit": "%",
            "message": _humidity_message(humidity),
            "variable_description": VARIABLE_DESCRIPTIONS["humidity"],
            "hourly_values": hourly_humidity,
        },
        "feels_like": {
            "value": feels_like,
            "unit": "°C",
            "message": _feels_like_message(temp, feels_like),
            "variable_description": VARIABLE_DESCRIPTIONS["feels_like"],
            "hourly_values": hourly_feels_like,
        },
        "wind": {
            "value": round(wind, 1) if wind is not None else None,
            "unit": "m/s",
            "direction": _wind_direction(wind_direction),
            "message": _wind_message(wind),
            "variable_description": VARIABLE_DESCRIPTIONS["wind"],
            "hourly_values": hourly_wind_speed,
        },
        "sunrise": {
            "value": "N/A",
            "unit": "",
            "message": "Sunrise data coming soon",
        },
        "uv_index": {
            "value": "N/A",
            "unit": "",
            "message": "uv_index data coming soon",
        },
        "visibility": {
            "value": "N/A",
            "unit": "",
            "message": "visibility data coming soon",
        },
        "pressure": {
            "value": (
                round(pressure / 100, 1)
                if current and current != 0 and pressure
                else None
            ),
            "unit": "hPa",
            "message": "",
            "variable_description": VARIABLE_DESCRIPTIONS["pressure"],
            "hourly_values": hourly_pressure,
        },
    }


def _wind_direction(degrees: float | None) -> str | None:
    if degrees is None:
        return None

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = math.floor((degrees % 360 + 22.5) / 45) % len(directions)
    return directions[index]


def _compute_feels_like(
    temp: float | None, humidity: float | None, wind: float | None
) -> float | None:
    """Calculate shaded apparent temperature using the Steadman approach."""
    if temp is None or humidity is None or wind is None:
        return None

    if not all(math.isfinite(value) for value in (temp, humidity, wind)):
        return None

    if not 0 <= humidity <= 100 or wind < 0:
        return None

    vapour_pressure = (
        (humidity / 100)
        * 6.105
        * math.exp((17.27 * temp) / (237.7 + temp))
    )
    apparent_temp = temp + 0.33 * vapour_pressure - 0.70 * wind - 4.0
    return round(apparent_temp, 1)


def _humidity_message(humidity: float | None) -> str:
    if humidity is None or not 0 <= humidity <= 100:
        return "No data"
    if humidity < 30:
        return "Low relative humidity"
    if humidity <= 60:
        return "Moderate relative humidity"
    if humidity <= 80:
        return "High relative humidity"
    return "Very high relative humidity"


def _feels_like_message(
    temp: float | None, feels_like: float | None
) -> str:
    """Describe the difference between air and apparent temperature."""
    if temp is None or feels_like is None:
        return "No data"
    if not math.isfinite(temp) or not math.isfinite(feels_like):
        return "No data"

    difference = feels_like - temp
    if difference <= -3:
        return "Feels significantly colder"
    if difference < -1:
        return "Feels slightly colder"
    if difference >= 3:
        return "Feels significantly warmer"
    if difference > 1:
        return "Feels slightly warmer"
    return "Feels similar to the air temperature"


def _wind_message(wind: float | None) -> str:
    """Describe wind speed using the Beaufort Wind Scale."""
    if wind is None or not math.isfinite(wind) or wind < 0:
        return "No data"
    if wind < 0.3:
        return "Calm"
    if wind < 1.6:
        return "Light air"
    if wind < 3.4:
        return "Light breeze"
    if wind < 5.5:
        return "Gentle breeze"
    if wind < 8.0:
        return "Moderate breeze"
    if wind < 10.8:
        return "Fresh breeze"
    if wind < 13.9:
        return "Strong breeze"
    if wind < 17.2:
        return "Near gale"
    if wind < 20.8:
        return "Gale"
    if wind < 24.5:
        return "Strong gale"
    if wind < 28.5:
        return "Storm"
    if wind < 32.7:
        return "Violent storm"
    return "Hurricane-force winds"
