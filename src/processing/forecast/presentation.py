from collections import defaultdict
from datetime import datetime
import logging

from src import time_utils
from src.processing.forecast.codes import compute_daily_code, compute_hourly_code

logger = logging.getLogger(__name__)


def build_hourly_forecast(current: dict, forecast: list[dict]) -> list[dict]:
    """Build hourly forecast cards, limited to 48 forecast hours."""
    hourly = [
        {
            "time_step_fr": current.get("time_step_fr"),
            "temperature_celsius": current.get("temperature_celsius"),
            "precipitation_mm": current.get("precipitation_mm"),
            "weather_code": compute_hourly_code(current),
        }
    ]

    for entry in forecast[:48]:
        hourly.append(
            {
                "time_step_fr": entry.get("time_step_fr"),
                "temperature_celsius": entry.get("temperature_celsius"),
                "precipitation_mm": entry.get("precipitation_mm"),
                "weather_code": compute_hourly_code(entry),
            }
        )
    return hourly


def _specify_today_past_hours(today: str) -> list[str]:
    """Return the past hourly timestamps for today that need coverage."""
    now = time_utils.current_utc_iso("hour")
    time_steps = []
    for hour in range(0, 23):
        time_stamp = today + "T" + f"{hour:02d}" + ":00:00Z"
        if time_stamp == now:
            break
        time_steps.append(time_stamp)
    return time_steps


def _get_past_hours(
    entries: list[dict],
    missing_hours: list[str],
) -> tuple[list[dict], list[str]]:
    """
    Select entries matching missing hourly timestamps.

    Returns the matched entries and timestamps still missing. Entries with a
    missing temperature do not count as covered.
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


def _discard_last_day_if_not_worth(
    data: list[dict],
    last_day: str,
    minimum_hours: int = 12,
) -> list[dict]:
    """Drop the final day when it has too few distinct hourly temperatures."""
    last_day_entries = [
        entry
        for entry in data
        if str(entry.get("time_step_fr", ""))[:10] == last_day
        and entry.get("temperature_celsius") is not None
    ]
    valid_hours = {str(entry["time_step_fr"])[:13] for entry in last_day_entries}

    if len(valid_hours) < minimum_hours:
        return [
            entry
            for entry in data
            if str(entry.get("time_step_fr", ""))[:10] != last_day
        ]
    return data


def build_daily_forecast(
    today_obs: list[dict],
    forecast: list[dict],
    today_forecast: list[dict],
) -> list[dict]:
    """Aggregate observed and forecast hours into daily min/max and condition."""
    daily = []
    today = time_utils.current_france_date_iso()
    last_day = forecast[-1]["time_step_fr"][0:10]

    missing_past_hours = _specify_today_past_hours(today)
    today_past_hours_observed, missing_past_hours = _get_past_hours(
        today_obs, missing_past_hours
    )
    forecasted_past_hours, missing_past_hours = _get_past_hours(
        today_forecast, missing_past_hours
    )

    if missing_past_hours:
        logger.warning(
            "Could not fill %d past hourly slots for %s: %s",
            len(missing_past_hours),
            today,
            missing_past_hours,
        )

    data = today_past_hours_observed + forecasted_past_hours + forecast
    data = _discard_last_day_if_not_worth(data, last_day)

    days = defaultdict(list)
    for entry in data:
        time_str = entry.get("time_step_fr", "")
        if not time_str:
            continue
        days[time_str[0:10]].append(entry)

    for date_key in sorted(days):
        entries = days[date_key]
        temps = [
            entry.get("temperature_celsius")
            for entry in entries
            if entry.get("temperature_celsius") is not None
        ]
        if not temps:
            continue

        if date_key == today:
            label = "Today"
        else:
            label = datetime.strptime(date_key, "%Y-%m-%d").strftime("%a %d")

        daily.append(
            {
                "day": label,
                "min": round(min(temps), 1),
                "max": round(max(temps), 1),
                "weather_code": compute_daily_code(entries),
            }
        )

    return daily
