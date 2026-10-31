"""
Analysis processor — computes forecast accuracy metrics by joining
silver.forecast_arome with silver.observations_hourly.

All heavy computation happens in SQL (indexed join + GROUP BY).
Python only post-processes the rows into the frontend response shape.

"""

import logging
import numpy as np
import math
from datetime import datetime, timedelta, timezone
from src.data.db import DatabaseConnection
import math
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

logger = logging.getLogger(__name__)

# Rain detection threshold — standard WMO definition
RAIN_THRESHOLD_MM = 0.1

        # fw.step,
        # fw.temp_forecast,
        # fw.wind_forecast,
        # fw.rain_forecast,
        # o.temperature_celsius   AS temp_observed,
        # o.wind_speed_m_per_s    AS wind_observed,
        # o.precipitation_mm      AS rain_observed

# ── SQL ────────────────────────────────────────────────────────────────────────

# We added: 'NaN'::double precision since currently in silver it is not well converted later on this should be removed and solved in silver
_ANALYSIS_SQL = """
WITH forecast_with_step AS (
    SELECT
        f.station_id,
        f.run_time,
        f.time_step_fr,
        f.temperature_celsius   AS temp_forecast,
        f.wind_speed_m_per_s    AS wind_forecast,
        f.precipitation_mm      AS rain_forecast,
        ROW_NUMBER() OVER (
            PARTITION BY f.station_id, f.run_time
            ORDER BY f.time_step_fr
        ) AS step
    FROM {forecast_table} f
    WHERE f.run_time >= %(date_from)s
      AND f.run_time <= %(date_to)s
      AND (%(station_id)s IS NULL OR f.station_id = %(station_id)s)
),
joined AS (
    SELECT
    fw.step,
    NULLIF(fw.temp_forecast, 'NaN'::double precision) AS temp_forecast,
    NULLIF(fw.wind_forecast, 'NaN'::double precision) AS wind_forecast,
    NULLIF(fw.rain_forecast, 'NaN'::double precision) AS rain_forecast,

    NULLIF(o.temperature_celsius, 'NaN'::double precision) AS temp_observed,
    NULLIF(o.wind_speed_m_per_s, 'NaN'::double precision) AS wind_observed,
    NULLIF(o.precipitation_mm, 'NaN'::double precision) AS rain_observed    
    
    FROM forecast_with_step fw
    JOIN {obs_table} o
      ON  o.station_id    = fw.station_id
      AND o.time_step_fr  = fw.time_step_fr

)
SELECT
    step,
    AVG(ABS(temp_forecast - temp_observed))                         AS temp_mae,
    SQRT(AVG(POWER(temp_forecast - temp_observed, 2)))              AS temp_rmse,
    AVG(temp_forecast - temp_observed)                              AS temp_bias,
    COUNT(*) FILTER (WHERE temp_forecast IS NOT NULL
                     AND temp_observed IS NOT NULL)                 AS n_temp_samples,
    
    AVG(ABS(wind_forecast - wind_observed))                         AS wind_mae,
    SQRT(AVG(POWER(wind_forecast - wind_observed, 2)))              AS wind_rmse,
    AVG(wind_forecast - wind_observed)                              AS wind_bias,
    COUNT(*) FILTER (WHERE wind_forecast IS NOT NULL
                     AND wind_observed IS NOT NULL)                 AS n_wind_samples,    
    
    SUM(CASE WHEN rain_forecast > %(rain_thresh)s
             AND rain_observed  > %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_tp,
    SUM(CASE WHEN rain_forecast > %(rain_thresh)s
             AND rain_observed <= %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_fp,
    SUM(CASE WHEN rain_forecast <= %(rain_thresh)s
             AND rain_observed  > %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_fn,
    SUM(CASE WHEN rain_forecast <= %(rain_thresh)s
             AND rain_observed <= %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_tn,
    COUNT(*) FILTER (WHERE rain_forecast IS NOT NULL
                     AND rain_observed IS NOT NULL)                  AS n_rain_samples
FROM joined
GROUP BY step
ORDER BY step
"""


# ── Database query ─────────────────────────────────────────────────────────────

        
def format_metric(value):
    return round(value * 100) if not math.isnan(value) else float("nan")

def _fetch_step_metrics(
    date_from: datetime,
    date_to: datetime,
    station_id: str | None,
    forecast_table: str,
    obs_table: str,
) -> list[dict]:
    """
    Runs the analysis SQL and returns one dict per forecast step.
    station_id=None means aggregate over all stations.
    """
    sql = _ANALYSIS_SQL.format(
        forecast_table=forecast_table,
        obs_table=obs_table,
    )
    params = {
        "date_from":    date_from,
        "date_to":      date_to,
        "station_id":   station_id,
        "rain_thresh":  RAIN_THRESHOLD_MM,
    }

    try:
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Analysis query failed: {e}")
        raise


# ── Metric helpers ─────────────────────────────────────────────────────────────

def _safe(value, decimals=2):
    """Rounds a value safely, returns None if None or NaN."""
    # if value is None:
    #     return None
    try:
        f = float(value)
        return round(f, decimals) if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _precision(tp, fp):
    return round(tp / (tp + fp), 3) if (tp + fp) > 0 else 0.0

def _recall(tp, fn):
    return round(tp / (tp + fn), 3) if (tp + fn) > 0 else 0.0

def _f1(precision, recall):
    if (precision + recall) == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 3)

def _specificity(tn, fp):
    return round(tn / (tn + fp), 3) if (tn + fp) > 0 else 0.0

def _balanced_accuracy(recall, specificity):
    return round((recall + specificity) / 2, 3)

# ── Insight sentence generators ────────────────────────────────────────────────

def _temp_insight(mae, rmse, bias):
    if mae is None:
        return "Insufficient data to evaluate temperature accuracy."
    if mae < 0.8:
        verdict = "excellent"
    elif mae < 1.5:
        verdict = "good"
    elif mae < 2.5:
        verdict = "moderate"
    else:
        verdict = "poor"

    bias_str = (
        f"The model has a warm bias of {abs(bias):.1f}°C." if bias > 0.5
        else f"The model has a cold bias of {abs(bias):.1f}°C." if bias < -0.5
        else "The model shows no systematic bias."
    )
    return (
        f"Temperature forecast accuracy is {verdict} "
        f"with a mean absolute error of {mae:.1f}°C. {bias_str}"
    )

def _wind_insight(mae, bias):
    if mae is None:
        return "Insufficient data to evaluate wind accuracy."
    if mae < 1.0:
        verdict = "excellent"
    elif mae < 2.0:
        verdict = "good"
    elif mae < 3.5:
        verdict = "moderate"
    else:
        verdict = "poor"

    bias_str = (
        f"The model tends to overestimate wind speed by {abs(bias):.1f} m/s."
        if bias > 0.5
        else f"The model tends to underestimate wind speed by {abs(bias):.1f} m/s."
        if bias < -0.5
        else "No systematic wind bias detected."
    )
    return (
        f"Wind speed accuracy is {verdict} "
        f"with a mean absolute error of {mae:.1f} m/s. {bias_str}"
    )

def _rain_insight(tp, fp, fn, f1):
    total_actual = tp + fn
    if total_actual == 0:
        return "No rain was observed in this period, so rain detection cannot be assessed."
    hit_rate = round(100 * tp / total_actual)
    verdict = "strong" if f1 >= 80 else "moderate" if f1 >= 55 else "weak"
    if fp > 2 * fn:
        issue = f"The main weakness is false alarms: rain forecast but not observed ({fp} cases)."
    elif fn > 2 * fp:
        issue = f"The main weakness is missed rain: observed but not forecast ({fn} cases)."
    else:
        issue = f"False alarms: {fp}, missed rain: {fn}."
    return (
        f"Rain detection is {verdict}: the model caught {hit_rate}% of observed rainy hours "
        f"({tp} of {total_actual}). {issue} Rain means at least 0.1 mm in the hour; each station, "
        "hour and forecast run counts as one sample."
    )

# def _rain_insight(tp, fp, fn, f1):
#     total_actual = tp + fn
#     if total_actual == 0:
#         return "No rain events observed in this period."
#     if f1 >= 80:
#         return (
#             f"Rain detection is strong — the model correctly identified "
#             f"{tp} out of {total_actual} rainy hours with only {fp} false alarms."
#         )
#     elif f1 >= 55:
#         return (
#             f"Rain detection is moderate — {tp} of {total_actual} rainy hours "
#             f"caught correctly, but {fp} false alarms and {fn} misses."
#         )
#     return (
#         f"Rain detection is poor — the model missed {fn} of {total_actual} "
#         f"rainy hours and produced {fp} false alarms."
#     )


# ── Response builders ──────────────────────────────────────────────────────────

def _build_temperature(rows: list[dict]) -> dict:
    """
    Builds temperature section from per-step rows.
    degradation: dict of step → mae for the frontend chart.
    overall metrics: averaged across all steps weighted by n_samples.
    """
    if not rows:
        return {"degradation": {}, "mae": None, "rmse": None,
                "bias": None, "insight": "No data available."}

    # import pdb
    # pdb.set_trace()
    # Weighted averages across steps
    total_n   = sum(r["n_temp_samples"] for r in rows)
    if total_n == 0:
        return {"degradation": {}, "mae": None, "rmse": None,
                "bias": None, "insight": "No data available."}
    else:    
        def weighted_average(rows, metric):
            valid_rows = [
                (float(r[metric]), float(r["n_temp_samples"]))
                for r in rows
                if r.get(metric) is not None
                and r.get("n_temp_samples") is not None
                and float(r["n_temp_samples"]) > 0
            ]
        
            total_n = sum(n for _, n in valid_rows)
        
            if total_n == 0:
                return None
        
            return sum(value * n for value, n in valid_rows) / total_n

        w_mae  = weighted_average(rows, "temp_mae")
        w_rmse = weighted_average(rows, "temp_rmse")
        w_bias = weighted_average(rows, "temp_bias")
        
        # w_mae     = sum(float(r["temp_mae"])  * r["n_temp_samples"] for r in rows) / total_n
        # w_rmse    = sum(float(r["temp_rmse"]) * r["n_temp_samples"] for r in rows) / total_n
        # w_bias    = sum(float(r["temp_bias"]) * r["n_temp_samples"] for r in rows) / total_n
    
        degradation = {
            int(r["step"]): _safe(r["temp_mae"])
            for r in rows if r["temp_mae"] is not None
        }
    
        mae  = _safe(w_mae)
        rmse = _safe(w_rmse)
        bias = _safe(w_bias)
    
        return {
            "degradation": degradation,
            "mae":         mae,
            "rmse":        rmse,
            "bias":        bias,
            "insight":     _temp_insight(mae, rmse, bias),
        }


def _build_wind(rows: list[dict]) -> dict:
    if not rows:
        return {"degradation": {}, "mae": None, "rmse": None,
                "bias": None, "insight": "No data available."}        

    total_n = sum(r["n_wind_samples"] for r in rows)
    if total_n == 0:
        return {"degradation": {}, "mae": None, "rmse": None,
                "bias": None, "insight": "No data available."}
    else:
        w_mae   = sum(float(r["wind_mae"])  * r["n_wind_samples"] for r in rows) / total_n
        w_rmse  = sum(float(r["wind_rmse"]) * r["n_wind_samples"] for r in rows) / total_n
        w_bias  = sum(float(r["wind_bias"]) * r["n_wind_samples"] for r in rows) / total_n
    
        degradation = {
            int(r["step"]): _safe(r["wind_mae"])
            for r in rows
        }
    
        mae  = _safe(w_mae)
        rmse = _safe(w_rmse)
        bias = _safe(w_bias)
    
        return {
            "degradation": degradation,
            "mae":         mae,
            "rmse":        rmse,
            "bias":        bias,
            "insight":     _wind_insight(mae, bias),
        }


def _build_rain(rows: list[dict]) -> dict:
    """
    Rain metrics are summed across all steps — not averaged.
    We want total confusion matrix counts for the whole period.
    """

    if not rows:
        return {"tp": None, "fp": None, "fn": None, "tn": None,
                "precision": None, "recall": None, "f1": None,
                "insight": "No data available."}
    total_n = sum(r["n_rain_samples"] for r in rows)
    if total_n == 0:
        return {"tp": None, "fp": None, "fn": None, "tn": None,
                "precision": None, "recall": None, "f1": None,
                "insight": "No data available."}
    else:
        # import pdb
        # pdb.set_trace()
        tp = sum(int(r["rain_tp"]) for r in rows)
        fp = sum(int(r["rain_fp"]) for r in rows)
        fn = sum(int(r["rain_fn"]) for r in rows)
        tn = sum(int(r["rain_tn"]) for r in rows)       
        
        # Reconstruct actual labels
        nb_samples = tp + tn + fp + fn
        
        
        y_true = (
            [1] * tp +
            [0] * tn +
            [0] * fp +
            [1] * fn
        )
        
        # Reconstruct predicted labels
        y_pred = (
            [1] * tp +
            [0] * tn +
            [1] * fp +
            [0] * fn
        )


        accuracy = format_metric(accuracy_score(y_true, y_pred))
        if np.isnan(accuracy):
            accuracy = None

        if len(np.unique(y_true)) < 2:
            balanced_accuracy  = None
        else:
            balanced_accuracy = format_metric(
                balanced_accuracy_score(y_true, y_pred)
            )
        
        prec = format_metric(
            precision_score(y_true, y_pred, zero_division=float("nan"))
        )
        if np.isnan(prec):
            prec = None
        
        rec = format_metric(
            recall_score(y_true, y_pred, zero_division=float("nan"))
        )
        if np.isnan(rec):
            rec = None
        
        
        f1 = format_metric(
            f1_score(y_true, y_pred, zero_division=float("nan"))
        )
        if np.isnan(f1):
            f1 = None

        # accuracy =  accuracy_score(y_true, y_pred) * 100
        # balanced_accuracy = balanced_accuracy_score(y_true, y_pred) * 100
        # prec   = round(precision_score(y_true, y_pred, zero_division=float("nan")) * 100)
        # rec    = round(recall_score(y_true, y_pred, zero_division=float("nan")) * 100)
        # f1     = round(f1_score(y_true, y_pred, zero_division=float("nan")) * 100)

        # prec   = round(_precision(tp, fp) * 100)
        # rec    = round(_recall(tp, fn) * 100)
        # f1     = round(_f1(prec, rec))
        specificity = _specificity(tn, fp) * 100
        if np.isnan(specificity ):
            specificity  = None
        # balanced_accuracy = _balanced_accuracy(rec, specificity)
        # import pdb
        # pdb.set_trace()
        return {
            "tp":        tp,
            "fp":        fp,
            "fn":        fn,
            "tn":        tn,
            "precision": prec,
            "recall":    rec,
            "f1":        f1,
            "specificity": specificity,
            "balanced_acc": balanced_accuracy,
            "accuracy": accuracy,
            "insight":   _rain_insight(tp, fp, fn, f1),
        }


# ── Main entry point ───────────────────────────────────────────────────────────

def compute_analysis(
    days: int,
    station_id: str | None,
    forecast_table: str,
    obs_table: str,
) -> dict:
    """
    Main entry point called by the API endpoint.

    Parameters
    ----------
    days        : number of past days to include (e.g. 7)
    station_id  : specific station or None for all stations
    forecast_table : fully qualified table name e.g. silver.forecast_arome
    obs_table   : fully qualified table name e.g. silver.observations_hourly

    Returns
    -------
    dict shaped for the frontend AnalysisPage
    """
    # date_to   = datetime.utcnow()
    date_to   = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    logger.info(
        f"Computing analysis: {days} days, "
        f"station={station_id or 'all'}, "
        f"{date_from.date()} → {date_to.date()}"
    )

    rows = _fetch_step_metrics(
        date_from=date_from,
        date_to=date_to,
        station_id=station_id,
        forecast_table=forecast_table,
        obs_table=obs_table,
    )

    if not rows:
        logger.warning("Analysis query returned no rows")

    return {
        "meta": {
            "days":       days,
            "station_id": station_id,
            "date_from":  date_from.isoformat(),
            "date_to":    date_to.isoformat(),
            # "n_runs":     len(set(
            #     # approximate — we don't have run_time in aggregated rows
            #     # the frontend shows days instead
            #     []
            # )),
        },
        "temperature": _build_temperature(rows),
        "wind":        _build_wind(rows),
        "rain":        _build_rain(rows),
    }