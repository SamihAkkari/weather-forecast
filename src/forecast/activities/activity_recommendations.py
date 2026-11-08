from typing import TypedDict

from src.forecast.activities.activity_config import ACTIVITIES_CFG, ActivityConfig


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


def _status(score: float) -> str:
    if score >= 0.9:
        return "dark_green"
    if score >= 0.8:
        return "green"
    if score >= 0.7:
        return "light_green"
    if score >= 0.6:
        return "yellow_green"
    if score >= 0.5:
        return "yellow"
    if score >= 0.4:
        return "yellow_orange"
    if score >= 0.3:
        return "orange"
    if score >= 0.2:
        return "dark_orange"
    if score >= 0.1:
        return "red"
    return "dark_red"


def _summary_message(params: dict[str, ParameterScore]) -> str:
    """Choose the worst parameter message, or the first message if all score well."""
    values = list(params.values())
    non_green = [parameter for parameter in values if parameter["score"] < 0.7]
    if non_green:
        worst = min(non_green, key=lambda parameter: parameter["score"])
        return worst["description"]
    return values[0]["description"] if values else ""


def _score_hour(
    entry: dict[str, object],
    activity_config: ActivityConfig,
) -> ActivityEvaluation:
    params: dict[str, ParameterScore] = {}
    scores = []
    for name, parameter in activity_config["parameters"].items():
        value = entry.get(parameter.input)
        if value is not None and not isinstance(value, (int, float)):
            raise TypeError(f"Expected a numeric value for weather field '{parameter.input}'")

        score, message = parameter.scorer(value)
        params[name] = {
            "score": score,
            "status": _status(score),
            "description": message,
        }
        scores.append(score)

    activity_score = min(scores)
    activity_status = _status(activity_score)
    return activity_score, activity_status, params


def build_activity(
    current: dict[str, object],
    forecast: list[dict[str, object]],
    activity: str,
) -> dict[str, object]:
    """
    This is the main function for the activities results shown on the frontend
    This function is called once for each activity
    """
    
    activity_config = ACTIVITIES_CFG.get(activity)
    if activity_config is None: # raise an error if the activity requested is not defined in ACTIVITIES_CFG
        available = ", ".join(sorted(ACTIVITIES_CFG))
        raise ValueError(f"Unknown activity '{activity}'. Available: {available}")

    score, status, params = _score_hour(current, activity_config)
    scored_forecast = _score_forecast_entries(forecast, activity_config)
    return {
        "id": activity_config["id"],
        "icon": activity_config["icon"],
        "label": activity_config["label"],
        "status": status,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": status,
            "score": score,
            "parameters": params,
        },
        "best_window": _find_best_windows(scored_forecast),
        "hourly": _build_hourly_scores(scored_forecast),
    }


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
    """Build frontend hourly values from pre-scored forecast entries."""
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
    """Return up to two consecutive windows of at least two hours scoring >= 0.7."""
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
        best_description = next(
            (
                parameter["description"]
                for parameter in window[0]["parameters"].values()
                if parameter["score"] >= 0.7
            ),
            "Good conditions",
        )
        result.append(
            {
                "from": from_time,
                "to": to_time,
                "reason": best_description,
            }
        )

    return result
