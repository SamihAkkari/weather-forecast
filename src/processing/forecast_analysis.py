"""
Analysis processor:   
computes forecast accuracy metrics by joining
silver.forecast_arome with silver.observations_hourly.

All heavy computation happens in SQL (indexed join + GROUP BY).
Python only post-processes the rows into the frontend response shape.

In this script I intentionally provide a seperate builder for each analysed variable
since I want a clear separation between them even if there are some similarities in some places
like between temperature and wind (for this scale only 3 parameters this is not a problem)

"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Mapping, Sequence
from src.data.db import fetch_dicts

# from src.data.db import DatabaseConnection

logger = logging.getLogger(__name__)

# =============================================================================
# Analysis definitions and response contracts
# =============================================================================

RAIN_THRESHOLD_MM = 0.1
NO_DATA_INSIGHT = "No data available."

@dataclass(frozen=True)
class TemperatureResult:
    """Frontend response contract for temperature analysis."""

    degradation: dict[int, float | None]
    mae: float | None
    rmse: float | None
    bias: float | None
    insight: str


@dataclass(frozen=True)
class WindResult:
    """Frontend response contract for wind analysis."""

    degradation: dict[int, float | None]
    mae: float | None
    rmse: float | None
    bias: float | None
    insight: str


@dataclass(frozen=True)
class RainResult:
    """Frontend response contract for rain-detection analysis."""

    tp: int | None
    fp: int | None
    fn: int | None
    tn: int | None
    precision: int | None
    recall: int | None
    f1: int | None
    specificity: float | None
    balanced_acc: int | None
    accuracy: int | None
    insight: str


@dataclass(frozen=True)
class AnalysisDefinition:
    """
    Connects an analysis key to its builder and output contract.
    """
    builder: Callable[[Sequence[Mapping[str, object]]], object]
    output_type: type


# The registry is populated after the individual builders are defined below.
# It is the single place to see which analyses are exposed by this processor.
# More details are provided below where this dictionary is populated
ANALYSIS_DEFINITIONS: dict[str, AnalysisDefinition]


# =============================================================================
# SQL
# =============================================================================

# TODO: Remove the NULLIF(..., 'NaN') workaround once NaN values are correctly
# normalised in the silver layer.
_ANALYSIS_SQL = """
WITH forecast_with_step AS (
    SELECT
        f.station_id,
        f.run_time,
        f.time_step_fr,
        f.temperature_celsius AS temp_forecast,
        f.wind_speed_m_per_s AS wind_forecast,
        f.precipitation_mm AS rain_forecast,
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
      ON o.station_id = fw.station_id
     AND o.time_step_fr = fw.time_step_fr
)
SELECT
    step,
    AVG(ABS(temp_forecast - temp_observed)) AS temp_mae,
    SQRT(AVG(POWER(temp_forecast - temp_observed, 2))) AS temp_rmse,
    AVG(temp_forecast - temp_observed) AS temp_bias,
    COUNT(*) FILTER (
        WHERE temp_forecast IS NOT NULL AND temp_observed IS NOT NULL
    ) AS n_temp_samples,

    AVG(ABS(wind_forecast - wind_observed)) AS wind_mae,
    SQRT(AVG(POWER(wind_forecast - wind_observed, 2))) AS wind_rmse,
    AVG(wind_forecast - wind_observed) AS wind_bias,
    COUNT(*) FILTER (
        WHERE wind_forecast IS NOT NULL AND wind_observed IS NOT NULL
    ) AS n_wind_samples,

    SUM(CASE WHEN rain_forecast > %(rain_thresh)s
              AND rain_observed > %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_tp,
    SUM(CASE WHEN rain_forecast > %(rain_thresh)s
              AND rain_observed <= %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_fp,
    SUM(CASE WHEN rain_forecast <= %(rain_thresh)s
              AND rain_observed > %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_fn,
    SUM(CASE WHEN rain_forecast <= %(rain_thresh)s
              AND rain_observed <= %(rain_thresh)s THEN 1 ELSE 0 END) AS rain_tn,
    COUNT(*) FILTER (
        WHERE rain_forecast IS NOT NULL AND rain_observed IS NOT NULL
    ) AS n_rain_samples
FROM joined
GROUP BY step
ORDER BY step
"""


def _fetch_step_metrics(
    date_from: datetime,
    date_to: datetime,
    station_id: str | None,
    forecast_table: str,
    obs_table: str,
) -> list[dict]:
    """Run the aggregation query and return one row per forecast step."""
    sql = _ANALYSIS_SQL.format(
        forecast_table=forecast_table,
        obs_table=obs_table,
    )
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "station_id": station_id,
        "rain_thresh": RAIN_THRESHOLD_MM,
    }
    return fetch_dicts(sql, params)
    # try:
    #     with DatabaseConnection() as conn:
    #         with conn.cursor() as cursor:
    #             cursor.execute(sql, params)
    #             columns = [column[0] for column in cursor.description]
    #             return [dict(zip(columns, row)) for row in cursor.fetchall()]
    # except Exception:
    #     logger.exception("Analysis query failed")
    #     raise


def _safe(value: object, decimals: int = 2) -> float | None:
    """Round a numeric value, returning None for missing or non-finite values."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, decimals) if math.isfinite(number) else None


def _weighted_average(
    rows: Sequence[Mapping[str, object]],
    metric_key: str,
    sample_count_key: str,
) -> float | None:
    """Calculate a sample-count-weighted average for one metric."""
    weighted_values: list[tuple[float, float]] = []

    for row in rows:
        value = _safe(row.get(metric_key), decimals=10)
        sample_count = _safe(row.get(sample_count_key), decimals=10)

        if value is not None and sample_count is not None and sample_count > 0:
            weighted_values.append((value, sample_count))

    total_samples = sum(count for _, count in weighted_values)
    if total_samples == 0:
        return None

    return sum(value * count for value, count in weighted_values) / total_samples


def _has_samples(
    rows: Sequence[Mapping[str, object]],
    sample_count_key: str,
) -> bool:
    return sum(float(row.get(sample_count_key) or 0) for row in rows) > 0


def _specificity(tn: int, fp: int) -> float:
    """Return specificity as a fraction rounded to three decimal places."""
    return round(tn / (tn + fp), 3) if (tn + fp) > 0 else 0.0


def _percentage(numerator: int, denominator: int) -> int | None:
    """Return a rounded percentage, or None when it is undefined."""
    if denominator == 0:
        return None
    return round(100 * numerator / denominator)


# =============================================================================
# Analysis-specific insight generators
# =============================================================================

def _temperature_insight(mae: float | None, bias: float | None) -> str:
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

    if bias is not None and bias > 0.5:
        bias_text = f"The model has a warm bias of {abs(bias):.1f}°C."
    elif bias is not None and bias < -0.5:
        bias_text = f"The model has a cold bias of {abs(bias):.1f}°C."
    else:
        bias_text = "The model shows no systematic bias."

    return (
        f"Temperature forecast accuracy is {verdict} with a mean absolute "
        f"error of {mae:.1f}°C. {bias_text}"
    )


def _wind_insight(mae: float | None, bias: float | None) -> str:
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

    if bias is not None and bias > 0.5:
        bias_text = (
            f"The model tends to overestimate wind speed by {abs(bias):.1f} m/s."
        )
    elif bias is not None and bias < -0.5:
        bias_text = (
            f"The model tends to underestimate wind speed by {abs(bias):.1f} m/s."
        )
    else:
        bias_text = "No systematic wind bias detected."

    return (
        f"Wind speed accuracy is {verdict} with a mean absolute error "
        f"of {mae:.1f} m/s. {bias_text}"
    )


def _rain_insight(tp: int, fp: int, fn: int, f1: int | None) -> str:
    total_actual = tp + fn
    if total_actual == 0:
        return (
            "No rain was observed in this period, so rain detection "
            "cannot be assessed."
        )

    hit_rate = round(100 * tp / total_actual)
    verdict = "strong" if f1 is not None and f1 >= 80 else (
        "moderate" if f1 is not None and f1 >= 55 else "weak"
    )

    if fp > 2 * fn:
        issue = (
            "The main weakness is false alarms: rain forecast but not "
            f"observed ({fp} cases)."
        )
    elif fn > 2 * fp:
        issue = (
            "The main weakness is missed rain: observed but not forecast "
            f"({fn} cases)."
        )
    else:
        issue = f"False alarms: {fp}, missed rain: {fn}."

    return (
        f"Rain detection is {verdict}: the model caught {hit_rate}% of "
        f"observed rainy hours ({tp} of {total_actual}). {issue} "
        "Rain means at least 0.1 mm in the hour; each station, hour and "
        "forecast run counts as one sample."
    )


# =============================================================================
# Analysis-specific builders
# =============================================================================

def _empty_temperature_result() -> TemperatureResult:
    return TemperatureResult(
        degradation={},
        mae=None,
        rmse=None,
        bias=None,
        insight=NO_DATA_INSIGHT,
    )


def _build_temperature(
    rows: Sequence[Mapping[str, object]],
) -> TemperatureResult:
    """Build temperature metrics; overall values are weighted by sample count."""
    if not rows or not _has_samples(rows, "n_temp_samples"):
        return _empty_temperature_result()

    mae = _safe(_weighted_average(rows, "temp_mae", "n_temp_samples"))
    rmse = _safe(_weighted_average(rows, "temp_rmse", "n_temp_samples"))
    bias = _safe(_weighted_average(rows, "temp_bias", "n_temp_samples"))

    degradation = {
        int(row["step"]): _safe(row.get("temp_mae"))
        for row in rows
        if row.get("temp_mae") is not None
    }

    return TemperatureResult(
        degradation=degradation,
        mae=mae,
        rmse=rmse,
        bias=bias,
        insight=_temperature_insight(mae, bias),
    )


def _empty_wind_result() -> WindResult:
    return WindResult(
        degradation={},
        mae=None,
        rmse=None,
        bias=None,
        insight=NO_DATA_INSIGHT,
    )


def _build_wind(rows: Sequence[Mapping[str, object]]) -> WindResult:
    """Build wind metrics; overall values are weighted by sample count."""
    if not rows or not _has_samples(rows, "n_wind_samples"):
        return _empty_wind_result()

    mae = _safe(_weighted_average(rows, "wind_mae", "n_wind_samples"))
    rmse = _safe(_weighted_average(rows, "wind_rmse", "n_wind_samples"))
    bias = _safe(_weighted_average(rows, "wind_bias", "n_wind_samples"))

    degradation = {
        int(row["step"]): _safe(row.get("wind_mae"))
        for row in rows
        if row.get("wind_mae") is not None
    }

    return WindResult(
        degradation=degradation,
        mae=mae,
        rmse=rmse,
        bias=bias,
        insight=_wind_insight(mae, bias),
    )


def _empty_rain_result() -> RainResult:
    return RainResult(
        tp=None,
        fp=None,
        fn=None,
        tn=None,
        precision=None,
        recall=None,
        f1=None,
        specificity=None,
        balanced_acc=None,
        accuracy=None,
        insight=NO_DATA_INSIGHT,
    )


def _build_rain(rows: Sequence[Mapping[str, object]]) -> RainResult:
    """
    Build rain metrics by summing confusion-matrix counts across all steps.

    Unlike temperature and wind, rain counts are totals, not averages.
    Calculating scores directly from the confusion matrix avoids rebuilding
    potentially large y_true and y_pred arrays in Python.
    """
    if not rows or not _has_samples(rows, "n_rain_samples"):
        return _empty_rain_result()

    tp = sum(int(row.get("rain_tp") or 0) for row in rows)
    fp = sum(int(row.get("rain_fp") or 0) for row in rows)
    fn = sum(int(row.get("rain_fn") or 0) for row in rows)
    tn = sum(int(row.get("rain_tn") or 0) for row in rows)

    precision = _percentage(tp, tp + fp)
    recall = _percentage(tp, tp + fn)
    f1 = _percentage(2 * tp, 2 * tp + fp + fn)
    accuracy = _percentage(tp + tn, tp + fp + fn + tn)
    specificity = _specificity(tn, fp) * 100

    # Balanced accuracy is undefined when the observed labels contain only
    # one class, matching the previous implementation's behaviour. Calculate
    # from the unrounded rates, then round only the final percentage.
    if (tp + fn) == 0 or (tn + fp) == 0:
        balanced_acc = None
    else:
        sensitivity_rate = tp / (tp + fn)
        specificity_rate = tn / (tn + fp)
        balanced_acc = round(
            (sensitivity_rate + specificity_rate) / 2 * 100
        )

    return RainResult(
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        precision=precision,
        recall=recall,
        f1=f1,
        specificity=specificity,
        balanced_acc=balanced_acc,
        accuracy=accuracy,
        insight=_rain_insight(tp, fp, fn, f1),
    )


# Central registry: 
# this registery combines all the variables we want to do anlaysis for
# for each parameter we define its: 
#   1. builder: the function that computes the metrics
#   2. output_type: the output format of the builder (declared in result dataclass above)
# We can easily add a new cariable here and assign its own builder and output type following the same structure
# This would be sufficient for the backend
ANALYSIS_DEFINITIONS = {
    "temperature": AnalysisDefinition(
        builder=_build_temperature,
        output_type=TemperatureResult,
    ),
    "wind": AnalysisDefinition(
        builder=_build_wind,
        output_type=WindResult,
    ),
    "rain": AnalysisDefinition(
        builder=_build_rain,
        output_type=RainResult,
    ),
}


# =============================================================================
# Public entry point
# =============================================================================

def compute_analysis(
    days: int,
    station_id: str | None,
    forecast_table: str,
    obs_table: str,
) -> dict:
    """
    Compute forecast accuracy analysis for the requested period.

    The returned dictionary preserves the frontend response structure:
    ``meta``, ``temperature``, ``wind`` and ``rain``.
    """
    if days <= 0:
        raise ValueError("days must be a positive integer")

    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    logger.info(
        "Computing analysis: %s days, station=%s, %s -> %s",
        days,
        station_id or "all",
        date_from.date(),
        date_to.date(),
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

    response = {
        "meta": {
            "days": days,
            "station_id": station_id,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        }
    }

    for analysis_key, definition in ANALYSIS_DEFINITIONS.items():
        result = definition.builder(rows)

        # This assertion catches accidental mismatches in the parameter expected result type.
        # For example temperature parameter results should follow what is declared in TemperatureResult 
        # So if the type of the results is different (some keys do not exist) this will raise an error.
        if not isinstance(result, definition.output_type):
            raise TypeError(
                f"{analysis_key} builder returned {type(result).__name__}; "
                f"expected {definition.output_type.__name__}."
            )

        response[analysis_key] = asdict(result)

    return response
