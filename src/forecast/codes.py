"""Map AROME forecast values to WMO weather codes.

The classification follows Open-Meteo's weather-code logic, adapted to the
fields available in this forecast. Visibility and freezing-rain data are not
available; CAPE is used as a proxy for convective precipitation.

Reference: https://github.com/open-meteo/open-meteo/blob/main/Sources/App/Helper/WeatherCode.swift
"""

from __future__ import annotations
import math

# AROME SP1 data and the classification thresholds use hourly intervals.
MODEL_DT_HOURS: float = 1.0


def _ok(*values) -> bool:
    """True if all values are not None and finite."""
    return all(v is not None and math.isfinite(float(v)) for v in values)


def _thunderstorm_probability(
    cape: float,
    precip: float,
    cloud_cover: float,
    gusts: float | None,
) -> float:
    """
    Simplified version of open-meteo calculateThunderstormProbability.
    We drop CIN, LiftedIndex and PBL since we don't have them.
    Without those terms the weights are renormalized automatically
    because we track accumulatedScore / totalWeight.
    """

    # Suppress the estimate when CAPE or cloud cover is too low.
    if cape <= 10.0:
        return 0.0
    if cloud_cover < 30.0:
        return 0.0

    # Normalize by included weights because several input fields are unavailable.
    accumulated = 0.0
    total_weight = 0.0

    # CAPE score (weight 0.25 in open-meteo)
    cape_weight = 0.25
    cape_score = max(0.0, min((cape - 300.0) / (2500.0 - 300.0), 1.0))
    accumulated += cape_score * cape_weight
    total_weight += cape_weight

    # Precipitation score (weight 0.25 in open-meteo)
    # Total precipitation includes non-convective precipitation, so we apply a penalty.
    precip_weight = 0.25
    reference_precip = 2.0 * MODEL_DT_HOURS  # 2 mm/h reference
    fallback_reference = reference_precip * 1.6
    precip_score = max(0.0, min(precip / fallback_reference, 1.0))
    accumulated += precip_score * precip_weight * 0.6
    total_weight += precip_weight * 0.6

    # Gust score (weight 0.075 in open-meteo)
    if _ok(gusts):
        gust_weight = 0.075
        gust_score = max(0.0, min((gusts - 5.0) / 13.0, 1.0))
        accumulated += gust_score * gust_weight
        total_weight += gust_weight

    probability = (accumulated / total_weight) * 100.0

    # Cloud cover dampening
    if cloud_cover >= 60.0:
        cloud_factor = 1.0
    else:
        cloud_factor = 0.6 + 0.4 * ((cloud_cover - 30.0) / 30.0)
    probability *= cloud_factor

    return max(0.0, min(probability, 100.0))


def compute_hourly_code(entry: dict) -> int:
    """
    Assigns a WMO weather code to a single forecast timestep.

    Logic follows open-meteo WeatherCode.calculate() order:
        1. Thunderstorm
        2. (Freezing rain   skipped, no data)
        3. Convective snow showers
        4. Rain showers (convective)
        5. Stratiform snowfall
        6. Stratiform rain / drizzle
        7. (Fog   skipped, no visibility data)
        8. Cloud cover
    """

    precip = entry.get("precipitation_mm")
    tsnowp = entry.get("snow_precipitation_mm")
    cape      = entry.get("cape_m2_s2")
    cloud = entry.get("total_cloud_cover")
    temp = entry.get("temperature_celsius")
    gusts = entry.get("wind_gust_m_per_s")

    precip_rate = precip / MODEL_DT_HOURS if _ok(precip) else None
    # At 100 kg/m^3, mm water equivalent is numerically equal to cm snow depth.
    snow_rate   = tsnowp / MODEL_DT_HOURS if _ok(tsnowp) else None

    # 1. Thunderstorm ────────────────────────────────────────────────────
    if _ok(cape, precip, cloud):
        prob = _thunderstorm_probability(cape, precip, cloud, gusts)
        if prob > 85:
            return 96   # thunderstorm strong
        if prob > 60:
            return 95   # thunderstorm slight or moderate

    # 2. Freezing rain   skipped (no categoricalFreezingRain) ───────────

    # 3 & 4. Convective precipitation   showers ─────────────────────────
    # Use CAPE as a proxy because convective precipitation is unavailable.
    is_convective = _ok(cape) and cape >= 800

    if is_convective:
        # Convective snow showers
        if _ok(snow_rate):
            if 0.01 <= snow_rate < 0.2:
                return 85   # slight snow showers
            if snow_rate >= 0.2:
                return 86   # heavy snow showers

        # Convective rain showers
        if _ok(precip_rate):
            if 1.3 <= precip_rate < 2.5:
                return 80   # slight rain showers
            if 2.5 <= precip_rate < 7.6:
                return 81   # moderate rain showers
            if precip_rate >= 7.6:
                return 82   # violent rain showers

    # 5. Stratiform snowfall ─────────────────────────────────────────────
    if _ok(snow_rate):
        if 0.01 <= snow_rate < 0.2:
            return 71   # slight snowfall
        if 0.2 <= snow_rate < 0.8:
            return 73   # moderate snowfall
        if snow_rate >= 0.8:
            return 75   # heavy snowfall

    # 6. Stratiform rain / drizzle ──────────────────────────────────────
    # open-meteo thresholds (mm/h):
    # 0.01–0.5  → drizzle light
    # 0.5–1.0   → drizzle moderate
    # 1.0–1.3   → drizzle dense
    # 1.3–2.5   → light rain
    # 2.5–7.6   → moderate rain
    # 7.6+      → heavy rain
    if _ok(precip_rate):
        if 0.01 <= precip_rate < 0.5:
            return 51   # light drizzle
        if 0.5 <= precip_rate < 1.0:
            return 53   # moderate drizzle
        if 1.0 <= precip_rate < 1.3:
            return 55   # dense drizzle
        if 1.3 <= precip_rate < 2.5:
            return 61   # light rain
        if 2.5 <= precip_rate < 7.6:
            return 63   # moderate rain
        if precip_rate >= 7.6:
            return 65   # heavy rain

    # 7. Fog   skipped (no visibility data) ─────────────────────────────

    # 8. Cloud cover ─────────────────────────────────────────────────────
    # open-meteo thresholds: 0–20 clear, 20–50 mainly clear,
    # 50–80 partly cloudy, 80+ overcast
    if _ok(cloud):
        if cloud < 20:
            return 0    # clear sky
        if cloud < 50:
            return 1    # mainly clear
        if cloud < 80:
            return 2    # partly cloudy
        return 3        # overcast

    # Use clear sky when no available field indicates another condition.
    return 0


def compute_daily_code(entries: list[dict]) -> int:
    """Return the most severe WMO code across the day's forecast entries."""
    if not entries:
        return 0

    def severity(code: int) -> int:
        if code >= 95: return 9   # thunderstorm
        if code in (85, 86): return 8  # snow showers
        if code in (80, 81, 82): return 7  # rain showers
        if code in (71, 73, 75, 77): return 6  # snowfall
        if code in (61, 63, 65, 66, 67): return 5  # rain
        if code in (51, 53, 55, 56, 57): return 4  # drizzle
        if code == 45: return 3   # fog
        if code == 3:  return 2   # overcast
        if code == 2:  return 1   # partly cloudy
        return 0

    return max((compute_hourly_code(e) for e in entries), key=severity)