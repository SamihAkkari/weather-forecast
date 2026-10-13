import math
import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

"""
This module contains all the metric computation logic.
It receives plain Python lists of dicts (already fetched from the DB)
and returns a dict shaped exactly like mockAnalysis on the frontend.

Keeping this logic here rather than in the API route means:
- The route stays thin and readable
- This logic is easy to test independently
- You can reuse it later if you add a batch analysis endpoint
"""

def _mae(errors: list[float]) -> float:
    """Mean Absolute Error — average of absolute differences."""
    if not errors:
        return 0.0
    return round(sum(abs(e) for e in errors) / len(errors), 2)

def _rmse(errors: list[float]) -> float:
    """Root Mean Square Error — penalises large errors more than MAE."""
    if not errors:
        return 0.0
    return round(math.sqrt(sum(e**2 for e in errors) / len(errors)), 2)

def _bias(errors: list[float]) -> float:
    """
    Mean signed error (forecast - observed).
    Positive bias means the model systematically overestimates.
    Negative bias means it underestimates.
    """
    if not errors:
        return 0.0
    return round(sum(errors) / len(errors), 2)

def _precision(tp: int, fp: int) -> float:
    """Of all the times the model said YES, how often was it right?"""
    return round(tp / (tp + fp), 2) if (tp + fp) > 0 else 0.0

def _recall(tp: int, fn: int) -> float:
    """Of all the times the answer was actually YES, how often did the model catch it?"""
    return round(tp / (tp + fn), 2) if (tp + fn) > 0 else 0.0

def _f1(precision: float, recall: float) -> float:
    """Harmonic mean of precision and recall. Balances both metrics into one."""
    if (precision + recall) == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 2)

def _temperature_insight(bias: float, mae: float) -> str:
    """
    Generates a human readable sentence based on the actual metric values.
    The thresholds here (1.0, 0.5) are reasonable for a NWP model over France
    but you can adjust them as you learn more about your model's behaviour.
    """
    if abs(bias) < 0.5:
        return f"The model is well calibrated with a near-zero bias of {bias:+.1f}°C and a MAE of {mae}°C."
    elif bias > 1.0:
        return f"The model consistently overestimates temperature with a warm bias of {bias:+.1f}°C and a MAE of {mae}°C."
    elif bias < -1.0:
        return f"The model consistently underestimates temperature with a cold bias of {bias:+.1f}°C and a MAE of {mae}°C."
    elif bias > 0:
        return f"The model shows a slight warm bias of {bias:+.1f}°C on average, with a MAE of {mae}°C."
    else:
        return f"The model shows a slight cold bias of {bias:+.1f}°C on average, with a MAE of {mae}°C."

def _detection_insight(variable: str, tp: int, fp: int, fn: int, f1: float) -> str:
    """Generates an insight sentence for binary detection (rain or sunshine)."""
    total_actual = tp + fn
    if total_actual == 0:
        return f"No {variable} events observed in this period."
    if f1 >= 0.85:
        return f"{variable.capitalize()} is well captured — the model correctly identified {tp} out of {total_actual} {variable} hours with only {fp} false alarms."
    elif f1 >= 0.65:
        return f"The model correctly caught {tp} out of {total_actual} {variable} hours but triggered {fp} false alarms."
    else:
        return f"The model struggles to detect {variable} — it missed {fn} out of {total_actual} {variable} hours and had {fp} false alarms."

def _is_rainy(precipitation_mm) -> bool:
    """A timestep is considered rainy if precipitation exceeds 0.1mm."""
    if precipitation_mm is None:
        return False
    return float(precipitation_mm) > 0.1

def _is_sunny(radiation_j_m2) -> bool:
    """
    A timestep is considered sunny if global radiation exceeds 120 W/m2 equivalent.
    Our column stores J/m2 per hour, so 120 W/m2 * 3600s = 432000 J/m2.
    Adjust this threshold based on what makes sense in your data.
    """
    if radiation_j_m2 is None:
        return False
    return float(radiation_j_m2) > 432000

# def analyse(
#     forecast: list[dict],
#     observations: list[dict]
# ) -> dict:
#     """
#     Main function. Joins forecast and observations on time_step_fr,
#     computes all metrics, and returns a dict shaped like mockAnalysis.
#     """
#     # import pdb
#     # pdb.set_trace()
#     # Index observations by time for fast lookup
#     obs_by_time = {row['time_step_fr']: row for row in observations}

#     # Build matched pairs — only keep timesteps present in both
#     comparison = []
#     temp_errors = []
#     rain_tp = rain_fp = rain_fn = rain_tn = 0
#     sun_tp = sun_fp = sun_fn = sun_tn = 0

#     # For degradation: group errors by horizon
#     # horizon is computed as hours since the first forecast timestep
#     if forecast:
#         first_time = forecast[0]['time_step_fr'].isoformat()

#     horizon_errors: dict[int, list[float]] = {}

#     for row in forecast:
#         time = row['time_step_fr'].isoformat()
#         obs = obs_by_time.get(time)
#         if obs is None:
#             continue  # no matching observation for this timestep, skip

#         f_temp = row['temperature_celsius']
#         o_temp = obs['temperature_celsius']

#         # Skip if either value is missing
#         if f_temp is None or o_temp is None:
#             continue

#         f_temp = float(f_temp)
#         o_temp = float(o_temp)
#         error = f_temp - o_temp
#         temp_errors.append(error)

#         comparison.append({
#             'time': time,
#             'forecast': round(f_temp, 1),
#             'observed': round(o_temp, 1),
#         })

#         # Degradation: compute horizon in hours from run start
#         horizon_h = int((datetime.fromisoformat(time)- datetime.fromisoformat(first_time)).total_seconds() / 3600)
#         if horizon_h not in horizon_errors:
#             horizon_errors[horizon_h] = []
#         horizon_errors[horizon_h].append(abs(error))

#         # Rain confusion matrix
#         f_rain = _is_rainy(row['precipitation_mm'])
#         o_rain = _is_rainy(obs['precipitation_mm'])
#         if f_rain and o_rain:     rain_tp += 1
#         elif f_rain and not o_rain: rain_fp += 1
#         elif not f_rain and o_rain: rain_fn += 1
#         else:                       rain_tn += 1

#         # Sunshine confusion matrix
#         f_sun = _is_sunny(row['global_radiation_j_m2'])
#         o_sun = _is_sunny(obs['global_radiation_j_m2'])
#         if f_sun and o_sun:       sun_tp += 1
#         elif f_sun and not o_sun: sun_fp += 1
#         elif not f_sun and o_sun: sun_fn += 1
#         else:                     sun_tn += 1

#     # Compute temperature metrics
#     mae  = _mae(temp_errors)
#     rmse = _rmse(temp_errors)
#     bias = _bias(temp_errors)

#     # Build degradation curve — average MAE per horizon bucket
#     degradation = [
#         {'horizon_h': h, 'mae': round(sum(errs) / len(errs), 2)}
#         for h, errs in sorted(horizon_errors.items())
#         if errs
#     ]

#     # Compute detection metrics
#     rain_prec = _precision(rain_tp, rain_fp)
#     rain_rec  = _recall(rain_tp, rain_fn)
#     rain_f1   = _f1(rain_prec, rain_rec)

#     sun_prec = _precision(sun_tp, sun_fp)
#     sun_rec  = _recall(sun_tp, sun_fn)
#     sun_f1   = _f1(sun_prec, sun_rec)

#     return {
#         'station_name': station_name,
#         'temperature': {
#             'comparison': comparison,
#             'mae': mae,
#             'rmse': rmse,
#             'bias': bias,
#             'degradation': degradation,
#             'insight': _temperature_insight(bias, mae),
#         },
#         'rain': {
#             'tp': rain_tp, 'fp': rain_fp,
#             'fn': rain_fn, 'tn': rain_tn,
#             'precision': rain_prec,
#             'recall': rain_rec,
#             'f1': rain_f1,
#             'insight': _detection_insight('rain', rain_tp, rain_fp, rain_fn, rain_f1),
#         },
#         'sunshine': {
#             'tp': sun_tp, 'fp': sun_fp,
#             'fn': sun_fn, 'tn': sun_tn,
#             'precision': sun_prec,
#             'recall': sun_rec,
#             'f1': sun_f1,
#             'insight': _detection_insight('sunshine', sun_tp, sun_fp, sun_fn, sun_f1),
#         }
#     }


def analyse(
    forecast: list[dict],
    observations: list[dict]
) -> dict:
    """
    Main function. Joins forecast and observations on time_step_fr,
    computes all metrics, and returns a dict shaped like mockAnalysis.
    """

    # if len(forecast) != len(observations):
    #     logger.error("forecast and observations should have the same size for the analyser to work")
    #     raise ValueError
    
    if forecast:
        first_time = forecast[0]['time_step_fr'].isoformat()

    # Index observations by time for fast lookup
    obs_by_time = {row['time_step_fr']: row for row in observations}
    horizon_errors: dict[int, list[float]] = {}
    
    rain_tp = rain_fp = rain_fn = rain_tn = 0
    sun_tp = sun_fp = sun_fn = sun_tn = 0

    for ind in range(len(forecast)):
        time = forecast[ind]['time_step_fr'].isoformat()
        corresponding_obs = obs_by_time.get(time)
        if corresponding_obs is None:
            continue  # no matching observation for this timestep, skip

        forecast_temp = forecast[ind]['temperature_celsius']
        observations_temp = corresponding_obs['temperature_celsius']

        # Skip if either value is missing
        if forecast_temp is None or observations_temp is None:
            continue

        f_temp = float(forecast_temp)
        o_temp = float(observations_temp)
        error = f_temp - o_temp

       # Degradation: compute horizon in hours from run start
        horizon_h = int((datetime.fromisoformat(time)- datetime.fromisoformat(first_time)).total_seconds() / 3600)
        if horizon_h not in horizon_errors:
            horizon_errors[horizon_h] = []
        horizon_errors[horizon_h].append(abs(error))

        # Rain confusion matrix
        f_rain = _is_rainy(forecast[ind]['precipitation_mm'])
        o_rain = _is_rainy(corresponding_obs['precipitation_mm'])
        if f_rain and o_rain:     rain_tp += 1
        elif f_rain and not o_rain: rain_fp += 1
        elif not f_rain and o_rain: rain_fn += 1
        else:                       rain_tn += 1

        # Sunshine confusion matrix
        f_sun = _is_sunny(forecast[ind]['global_radiation_j_m2'])
        o_sun = _is_sunny(corresponding_obs['global_radiation_j_m2'])
        if f_sun and o_sun:       sun_tp += 1
        elif f_sun and not o_sun: sun_fp += 1
        elif not f_sun and o_sun: sun_fn += 1
        else:                     sun_tn += 1

    return {
        'temperature': {
            'degradation': horizon_errors
        },
        'rain': {
            'tp': rain_tp, 'fp': rain_fp,
            'fn': rain_fn, 'tn': rain_tn,
        },
        'sunshine': {
            'tp': sun_tp, 'fp': sun_fp,
            'fn': sun_fn, 'tn': sun_tn,
        }
    }

def aggregate(per_run_analysis):
    # --- temperature (average) ---
    temp_sum = defaultdict(float)
    temp_count = defaultdict(int)

    # --- rain & sunshine (sum) ---
    rain = defaultdict(int)
    sunshine = defaultdict(int)

    for run in per_run_analysis:
        # --- temperature ---
        for k, v_list in run.get("temperature", {}).get("degradation", {}).items():
            if v_list:  # safety check
                temp_sum[k] += v_list[0]
                temp_count[k] += 1

        # --- rain ---
        for key, value in run.get("rain", {}).items():
            rain[key] += value

        # --- sunshine ---
        for key, value in run.get("sunshine", {}).items():
            sunshine[key] += value

    # --- compute averages ---
    temperature_avg = {
        k: temp_sum[k] / temp_count[k]
        for k in temp_sum
        if temp_count[k] > 0
    }

    return {
        "temperature": {"degradation": temperature_avg},
        "rain": dict(rain),
        "sunshine": dict(sunshine),
    }