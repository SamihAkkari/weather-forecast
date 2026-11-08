"""Build activity recommendations from current and forecast conditions."""

from collections.abc import Callable
from typing import TypedDict

import src.processing.activity_scoring as activity_scoring


class ActivityParameter(TypedDict):
    name: str
    scorer_function: Callable[..., tuple[float, str]]
    scorer_function_inputs: list[str]


class ActivityConfig(TypedDict):
    id: str
    icon: str
    label: str
    parameters: list[ActivityParameter]


class ParameterScore(TypedDict):
    score: float
    status: str
    description: str


ActivityEvaluation = tuple[float, str, dict[str, ParameterScore]]


class ScoredHour(TypedDict):
    entry: dict[str, object]
    score: float
    status: str
    parameters: dict[str, ParameterScore]

def _activity_representative_score(scores: list[float]) -> float:
    return min(scores)

def _activity_status(scores: list[float] | float) -> str:
    """
    Combines multiple parameter scores into one overall status.
    The weakest parameter drives the overall status   a chain is only
    as strong as its weakest link. This matches how real conditions work:
    perfect temperature doesn't help if it's pouring rain.
    """
    if isinstance(scores, list):
        representative_score = _activity_representative_score(scores)
    elif isinstance(scores, float):
        representative_score  = scores
    else:
        raise TypeError("Activity scores must be a list of floats or a float")
    return _status(representative_score)

def _param(score: float, status: str, description: str) -> ParameterScore:
    return {"score": score, "status": status, "description": description}

def _status(score: float) -> str:
    if score >= 0.9: return "dark_green"
    if score >= 0.8: return "green"
    if score >= 0.7: return "light_green"
    if score >= 0.6: return "yellow_green"
    if score >= 0.5: return "yellow"
    if score >= 0.4: return "yellow_orange"
    if score >= 0.3: return "orange"
    if score >= 0.2: return "dark_orange"
    if score >= 0.1: return "red"
    return "dark_red"


# ── Summary message builder ────────────────────────────────────────────────────
def _summary_message(params: dict) -> str:
    """
    Builds the one-line summary shown in the LifestyleWidget card.
    Shows the worst parameter description if status is not all green,
    otherwise shows the best positive message.
    """
    values = list(params.values())
    non_green = [p for p in values if p["score"] < 0.7]
    if non_green:
        worst = min(non_green, key=lambda p: p["score"])
        return worst["description"]
    return values[0]["description"] if values else ""


# ── Activities configurations ──────────────────────────────────────────────────────────
ACTIVITIES_CFG: dict[str, ActivityConfig] = {
    "cycling":{
        "id": "cycling",
        "icon": "🚴",
        "label": "Cycling",
        "parameters":[
            {"name": "temperature", "scorer_function": activity_scoring.score_temp_cycling, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": activity_scoring.score_wind_cycling, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "gust", "scorer_function": activity_scoring.score_gust_cycling, "scorer_function_inputs": ["wind_gust_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_cycling, "scorer_function_inputs": ["precipitation_mm"]},
            {"name": "snow", "scorer_function": activity_scoring.score_snow_cycling, "scorer_function_inputs": ["snow_precipitation_mm"]}
            ]
        },
    "running":{
        "id": "running",
        "icon": "🏃",
        "label": "Running",
        "parameters":[
            {"name": "temperature", "scorer_function": activity_scoring.score_temp_running, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": activity_scoring.score_wind_running, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_running, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "hiking":{
        "id": "hiking",
        "icon": "🥾",
        "label": "Hiking",
        "parameters":[
            {"name": "temperature", "scorer_function": activity_scoring.score_temp_hiking, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": activity_scoring.score_wind_hiking, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "gust", "scorer_function": activity_scoring.score_gust_hiking, "scorer_function_inputs": ["wind_gust_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_hiking, "scorer_function_inputs": ["precipitation_mm"]},
            {"name": "snow", "scorer_function": activity_scoring.score_snow_hiking, "scorer_function_inputs": ["snow_precipitation_mm"]}
            ]
        },
    "picnic":{
        "id": "picnic",
        "icon": "🧺",
        "label": "Picnic",
        "parameters":[
            {"name": "temperature", "scorer_function": activity_scoring.score_temp_picnic, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": activity_scoring.score_wind_picnic, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_picnic, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "fishing":{
        "id": "fishing",
        "icon": "🎣",
        "label": "Fishing",
        "parameters":[
            {"name": "wind", "scorer_function": activity_scoring.score_wind_fishing, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_fishing, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "photography":{
        "id": "photography",
        "icon": "📷",
        "label": "Photography",
        "parameters":[
            {"name": "cloud_cover", "scorer_function": activity_scoring.score_cloud_photography, "scorer_function_inputs": ["total_cloud_cover"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_photography, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "stargazing":{
        "id": "stargazing",
        "icon": "📷",
        "label": "Stargazing",
        "parameters":[
            {"name": "cloud_cover", "scorer_function": activity_scoring.score_cloud_stargazing, "scorer_function_inputs": ["total_cloud_cover"]},
            {"name": "humidity", "scorer_function": activity_scoring.score_humidity_stargazing, "scorer_function_inputs": ["humidity_percentage"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_stargazing, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "gardening":{
        "id": "gardening",
        "icon": "🌱",
        "label": "Gardening",
        "parameters":[
            {"name": "temperature", "scorer_function": activity_scoring.score_temp_gardening, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_gardening, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "clothing":{
        "id": "clothing",
        "icon": "🧥",
        "label": "Clothing",
        "parameters":[
            {"name": "temperature", "scorer_function": activity_scoring.score_temp_clothing, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": activity_scoring.score_wind_clothing, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_clothing, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "driving":{
        "id": "driving",
        "icon": "🚗",
        "label": "Driving",
        "parameters":[
            {"name": "snow", "scorer_function": activity_scoring.score_snow_driving, "scorer_function_inputs": ["snow_precipitation_mm"]},
            {"name": "wind", "scorer_function": activity_scoring.score_wind_driving, "scorer_function_inputs": ["wind_gust_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_driving, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "dogwalking":{
        "id": "dogwalking",
        "icon": "🐕",
        "label": "Dogwalking",
        "parameters":[
            {"name": "temperature", "scorer_function": activity_scoring.score_temp_dogwalk, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": activity_scoring.score_wind_dogwalk, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": activity_scoring.score_rain_dogwalk, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    }

def _score_hour(
    entry: dict[str, object],
    activity_config: ActivityConfig,
) -> ActivityEvaluation:
    activity_parameters_list = activity_config["parameters"] # list of dictionary
    params = {}
    tmp_list_os_scores = []
    for parameter in activity_parameters_list:
        parameter_name = parameter["name"]
        parameter_scorer_function = parameter["scorer_function"]
        parameter_scorer_function_inputs = parameter["scorer_function_inputs"]
        
        inputs = [entry.get(inpt) for inpt in parameter_scorer_function_inputs]
        
        score_value, message = parameter_scorer_function(*inputs)
        status = _status(score_value)
        
        params[parameter_name] = _param(score_value, status, message)
        tmp_list_os_scores.append(score_value)
    
    activity_score = _activity_representative_score(tmp_list_os_scores)
    activity_status = _activity_status(activity_score)

    return activity_score, activity_status, params


def build_activity(
    current: dict[str, object],
    forecast: list[dict[str, object]],
    activity: str,
) -> dict[str, object]:
    activity_config = ACTIVITIES_CFG.get(activity)
    if activity_config is None:
        available = ", ".join(sorted(ACTIVITIES_CFG))
        raise ValueError(f"Unknown activity '{activity}'. Available: {available}")
        
    idd = activity_config["id"]
    icon = activity_config["icon"]
    label = activity_config["label"]
    score, status, params = _score_hour(current, activity_config)
    scored_forecast = _score_forecast_entries(forecast, activity_config)
    return {
        "id": idd, "icon": icon, "label": label,
        "status": status,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": status, "score": score,
            "parameters": params
        },
        "best_window": _find_best_windows(scored_forecast),
        "hourly": _build_hourly_scores(scored_forecast),
    }


# ── Generic hourly builder ─────────────────────────────────────────────────────

def _score_forecast_entries(
    forecast: list[dict[str, object]],
    activity_config: ActivityConfig,
) -> list[ScoredHour]:
    """Score each forecast hour once for both the timeline and best windows."""
    scored_hours = []
    for entry in forecast[:48]:
        score, status, parameters = _score_hour(entry, activity_config)
        scored_hours.append(
            {
                "entry": entry,
                "score": score,
                "status": status,
                "parameters": parameters,
            }
        )
    return scored_hours


def _build_hourly_scores(
    scored_hours: list[ScoredHour],
) -> list[dict[str, object]]:
    """
    Build frontend hourly values from pre-scored forecast entries.
    """
    return [
        {
            "time": str(scored_hour["entry"].get("time_step_fr", "")),
            "score": round(scored_hour["score"], 2),
            "status": scored_hour["status"],
            "parameters": scored_hour["parameters"],
        }
        for scored_hour in scored_hours
    ]


def _find_best_windows(
    scored_hours: list[ScoredHour],
) -> list[dict[str, str]]:
    """
    Finds consecutive green windows in the forecast.
    Returns up to 2 windows where score >= 0.7 for at least 2 hours.
    A new window starts when score drops below 0.7.
    """
    windows = []
    current_window = []
    for scored_hour in scored_hours:
        if scored_hour["score"] >= 0.7:
            current_window.append(scored_hour)
        else:
            if len(current_window) >= 2:
                windows.append(current_window)
            current_window = []

    if len(current_window) >= 2:
        windows.append(current_window)

    result = []
    for window in windows[:2]:
        from_time = str(window[0]["entry"].get("time_step_fr", ""))
        to_time = str(window[-1]["entry"].get("time_step_fr", ""))
        best_desc = next(
            (
                parameter["description"]
                for parameter in window[0]["parameters"].values()
                if parameter["score"] >= 0.7
            ),
            "Good conditions"
        )
        result.append({
            "from":   from_time,
            "to":     to_time,
            "reason": best_desc,
        })

    return result